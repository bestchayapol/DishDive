package repository

import (
	"github.com/bestchayapol/DishDive/internal/entities"
)

type RecommendRepository interface {
	// Unified Settings (New approach)
	GetUserSettings(userID uint) ([]entities.PreferenceBlacklist, error)
	GetAllKeywordsWithUserSettings(userID uint) ([]entities.PreferenceBlacklist, error)
	BulkUpdateUserSettings(userID uint, settings []entities.PreferenceBlacklist) error

	// Reviews
	GetDishReviewPage(dishID uint) (*entities.Dish, *entities.Restaurant, error)
	SubmitReview(userID uint, dishID uint, resID uint, reviewText string) error

	// Keyword lookup
	GetKeywordByID(keywordID uint) (entities.Keyword, error)
	GetKeywordsByCategory(categories []string) ([]entities.Keyword, error)
}
