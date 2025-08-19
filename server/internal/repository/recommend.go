package repository

import (
    "github.com/bestchayapol/DishDive/internal/entities"
)

type RecommendRepository interface {
    // Preference/Blacklist
    GetPreferenceKeywordsByUser(userID uint) ([]entities.Keyword, error)
    SetPreferenceForKeyword(userID uint, keywordID uint, isPreferred bool, sentimentThreshold float64) error

    GetBlacklistKeywordsByUser(userID uint) ([]entities.Keyword, error)
    SetBlacklistForKeyword(userID uint, keywordID uint, isBlacklisted bool, sentimentThreshold float64) error

    // Reviews
    GetDishReviewPage(dishID uint) (*entities.Dish, *entities.Restaurant, error)
    SubmitReview(userID uint, dishID uint, resID uint, reviewText string) error
}