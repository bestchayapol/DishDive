package repository

import (
	"github.com/bestchayapol/DishDive/internal/entities"
)

type RecommendRepository interface {
	// Preference/Blacklist
	GetPreferencesByUser(userID uint) ([]entities.PreferenceBlacklist, error)
	SetPreference(userID, keywordID uint, threshold float64) error
	GetBlacklistByUser(userID uint) ([]entities.PreferenceBlacklist, error)
	SetBlacklist(userID, keywordID uint, threshold float64) error

	// Reviews
	GetDishReviewPage(dishID uint) (*entities.Dish, *entities.Restaurant, error)
	SubmitReview(userID uint, dishID uint, resID uint, reviewText string) error

	// Keyword lookup
	GetKeywordByID(keywordID uint) (entities.Keyword, error)
}
