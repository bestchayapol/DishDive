package service

import (
	"github.com/bestchayapol/DishDive/internal/dtos"
)

type RecommendService interface {
	// New unified settings API
	GetUserSettings(userID uint) (dtos.UserSettingsResponse, error)
	UpdateUserSettings(userID uint, req dtos.BulkUpdateSettingsRequest) error

	// Reviews and recommendations
	GetDishReviewPage(dishID uint) (dtos.DishReviewPageResponse, error)
	SubmitReview(req dtos.SubmitReviewRequest) (dtos.SubmitReviewResponse, error)
	GetRecommendedDishes(userID uint, resID *uint) ([]dtos.RestaurantMenuItemResponse, error)
	HasReviewExtract(sourceID uint, sourceType string) (bool, error)
	HasNormalizedReview(sourceID uint) (bool, error)
	GetLatestReviewExtract(sourceID uint, sourceType string) (string, error)
}
