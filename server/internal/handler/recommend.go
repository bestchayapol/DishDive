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

// Get preference keywords
func (h *RecommendHandler) GetPreferenceKeywords(c *fiber.Ctx) error {
	userID, err := strconv.Atoi(c.Params("userID"))
	if err != nil {
		return err
	}

	resp, err := h.recommendService.GetPreferenceKeywords(uint(userID))
	if err != nil {
		return err
	}
	return c.JSON(resp)
}

// Set preference
func (h *RecommendHandler) SetPreference(c *fiber.Ctx) error {
	userID, err := strconv.Atoi(c.Params("userID"))
	if err != nil {
		return err
	}

	var req dtos.SetPreferenceRequest
	if err := c.BodyParser(&req); err != nil {
		return err
	}

	err = h.recommendService.SetPreference(uint(userID), req)
	if err != nil {
		return err
	}
	return c.SendStatus(fiber.StatusOK)
}

// Get blacklist keywords
func (h *RecommendHandler) GetBlacklistKeywords(c *fiber.Ctx) error {
	userID, err := strconv.Atoi(c.Params("userID"))
	if err != nil {
		return err
	}

	resp, err := h.recommendService.GetBlacklistKeywords(uint(userID))
	if err != nil {
		return err
	}
	return c.JSON(resp)
}

// Set blacklist
func (h *RecommendHandler) SetBlacklist(c *fiber.Ctx) error {
	userID, err := strconv.Atoi(c.Params("userID"))
	if err != nil {
		return err
	}

	var req dtos.SetBlacklistRequest
	if err := c.BodyParser(&req); err != nil {
		return err
	}

	err = h.recommendService.SetBlacklist(uint(userID), req)
	if err != nil {
		return err
	}
	return c.SendStatus(fiber.StatusOK)
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

	resp, err := h.recommendService.GetRecommendedDishes(uint(userID))
	if err != nil {
		return err
	}
	return c.JSON(resp)
}
