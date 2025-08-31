package service

import (
	"github.com/bestchayapol/DishDive/internal/dtos"
)

type RecommendService interface {
    GetPreferenceKeywords(userID uint) ([]dtos.PreferenceKeywordResponse, error)
    SetPreference(userID uint, req dtos.SetPreferenceRequest) error
    GetBlacklistKeywords(userID uint) ([]dtos.BlacklistKeywordResponse, error)
    SetBlacklist(userID uint, req dtos.SetBlacklistRequest) error
    GetDishReviewPage(dishID uint) (dtos.DishReviewPageResponse, error)
    SubmitReview(req dtos.SubmitReviewRequest) (dtos.SubmitReviewResponse, error)
    GetRecommendedDishes(userID uint, resID *uint) ([]dtos.RestaurantMenuItemResponse, error) // Changed return type and added resID
}