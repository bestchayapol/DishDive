package handler

import (
	"strconv"

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
