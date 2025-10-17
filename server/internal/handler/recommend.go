package handler

import (
	"encoding/json"
	"strconv"

	"os"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/service"
	"github.com/gofiber/fiber/v2"
)

type RecommendHandler struct {
	recommendService service.RecommendService
}

func NewRecommendHandler(recommendService service.RecommendService) *RecommendHandler {
	return &RecommendHandler{recommendService: recommendService}
}

// New unified settings endpoints
func (h *RecommendHandler) GetUserSettings(c *fiber.Ctx) error {
	userID, err := strconv.Atoi(c.Params("userID"))
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid user ID"})
	}

	resp, err := h.recommendService.GetUserSettings(uint(userID))
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
	}
	return c.JSON(resp)
}

func (h *RecommendHandler) UpdateUserSettings(c *fiber.Ctx) error {
	userID, err := strconv.Atoi(c.Params("userID"))
	if err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid user ID"})
	}

	var req dtos.BulkUpdateSettingsRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid request body"})
	}

	err = h.recommendService.UpdateUserSettings(uint(userID), req)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
	}
	return c.JSON(fiber.Map{"success": true})
}

// Get dish review page
func (h *RecommendHandler) GetDishReviewPage(c *fiber.Ctx) error {
	dishID, err := strconv.Atoi(c.Params("dishID"))
	if err != nil {
		return err
	}

	resp, err := h.recommendService.GetDishReviewPage(uint(dishID))
	if err != nil {
		return err
	}
	return c.JSON(resp)
}

// Submit review
func (h *RecommendHandler) SubmitReview(c *fiber.Ctx) error {
	var req dtos.SubmitReviewRequest
	if err := c.BodyParser(&req); err != nil {
		return err
	}

	resp, err := h.recommendService.SubmitReview(req)
	if err != nil {
		return err
	}
	return c.JSON(resp)
}

// Get recommended dishes
func (h *RecommendHandler) GetRecommendedDishes(c *fiber.Ctx) error {
	userID, err := strconv.Atoi(c.Params("userID"))
	if err != nil {
		return err
	}

	resIDParam := c.Query("resID")
	var resID *uint
	if resIDParam != "" {
		resIDInt, err := strconv.Atoi(resIDParam)
		if err != nil {
			return err
		}
		resIDUint := uint(resIDInt)
		resID = &resIDUint
	}

	resp, err := h.recommendService.GetRecommendedDishes(uint(userID), resID)
	if err != nil {
		return err
	}
	return c.JSON(resp)
}

// Check if a review extract exists for a given review_id
func (h *RecommendHandler) GetReviewExtractStatus(c *fiber.Ctx) error {
	id, err := strconv.Atoi(c.Query("review_id", ""))
	if err != nil || id <= 0 {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "missing or invalid review_id"})
	}
	found, err := h.recommendService.HasReviewExtract(uint(id), "user")
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
	}
	return c.JSON(dtos.ReviewExtractStatusResponse{ReviewID: uint(id), SourceType: "user", Found: found})
}

func (h *RecommendHandler) GetReviewNormalizationStatus(c *fiber.Ctx) error {
	id, err := strconv.Atoi(c.Query("review_id", ""))
	if err != nil || id <= 0 {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "missing or invalid review_id"})
	}
	norm, err := h.recommendService.HasNormalizedReview(uint(id))
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
	}
	return c.JSON(fiber.Map{"review_id": id, "normalized": norm})
}

// Combined processing status for a user-submitted review
func (h *RecommendHandler) GetReviewProcessingStatus(c *fiber.Ctx) error {
	id, err := strconv.Atoi(c.Query("review_id", ""))
	if err != nil || id <= 0 {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "missing or invalid review_id"})
	}
	extractFound, err := h.recommendService.HasReviewExtract(uint(id), "user")
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
	}
	norm, err := h.recommendService.HasNormalizedReview(uint(id))
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
	}
	status := "pending"
	if extractFound { status = "extracted" }
	if norm { status = "normalized" }
	return c.JSON(fiber.Map{
		"review_id": id,
		"extract_found": extractFound,
		"normalized": norm,
		"status": status,
	})
}

// Return selected environment variables (masked) to verify server config
func (h *RecommendHandler) GetEnvStatus(c *fiber.Ctx) error {
	mask := func(s string) string {
		if len(s) <= 6 {
			return "***"
		}
		return s[:3] + "***" + s[len(s)-3:]
	}
	resp := fiber.Map{
		"PG_HOST": os.Getenv("PG_HOST"),
		"PG_PORT": os.Getenv("PG_PORT"),
		"PG_USER": os.Getenv("PG_USER"),
		"PG_DATABASE": os.Getenv("PG_DATABASE"),
		"OPENAI_MODEL": os.Getenv("OPENAI_MODEL"),
		"OPENAI_API_KEY": mask(os.Getenv("OPENAI_API_KEY")),
		"PYTHON_EXEC": os.Getenv("PYTHON_EXEC"),
	}
	return c.JSON(resp)
}

// Diagnostic: return the latest stored extraction JSON for a given review_id
func (h *RecommendHandler) GetLatestReviewExtract(c *fiber.Ctx) error {
	id, err := strconv.Atoi(c.Query("review_id", ""))
	if err != nil || id <= 0 {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "missing or invalid review_id"})
	}
	raw, err := h.recommendService.GetLatestReviewExtract(uint(id), "user")
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": err.Error()})
	}
	// Try to decode as JSON array to avoid double-encoding; fallback to raw string
	var arr []any
	if err := json.Unmarshal([]byte(raw), &arr); err == nil {
		return c.JSON(fiber.Map{"review_id": id, "items": arr})
	}
	return c.JSON(fiber.Map{"review_id": id, "raw": raw})
}
