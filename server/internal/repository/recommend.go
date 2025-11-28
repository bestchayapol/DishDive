package repository

import (
	"github.com/bestchayapol/DishDive/internal/entities"
)

type RecommendRepository interface {
	// Unified Settings (New approach)
	GetUserSettings(userID uint) ([]entities.PreferenceBlacklist, error)
	GetAllKeywordsWithUserSettings(userID uint) ([]entities.PreferenceBlacklist, error)
	// Detailed keyword + settings (avoids N+1 lookups)
	GetAllKeywordSettingsDetailed(userID uint) ([]KeywordSettingRow, error)
	BulkUpdateUserSettings(userID uint, settings []entities.PreferenceBlacklist) error

	// Reviews
	GetDishReviewPage(dishID uint) (*entities.Dish, *entities.Restaurant, error)
	SubmitReview(userID uint, dishID uint, resID uint, reviewText string) (uint, error)
	HasReviewExtract(sourceID uint, sourceType string) (bool, error)
	HasNormalizedReview(sourceID uint) (bool, error)

	// Extraction results
	UpsertReviewExtract(sourceID uint, sourceType string, dataExtract string) error
	GetLatestReviewExtract(sourceID uint, sourceType string) (string, error)

	// Normalization helpers
	EnsureReviewDish(sourceID uint, dishID uint, resID uint) (*entities.ReviewDish, error)
	FindKeywordByName(name string) (*entities.Keyword, error)
	EnsureReviewDishKeyword(reviewDishID uint, keywordID uint) error
	FindOrCreateKeyword(name string, category string, sentiment string) (*entities.Keyword, error)
	BumpDishKeyword(dishID uint, keywordID uint, delta int) error
	RecomputeScoresAndRestaurants() error

	// Keyword lookup
	GetKeywordByID(keywordID uint) (entities.Keyword, error)
	GetKeywordsByCategory(categories []string) ([]entities.Keyword, error)
	// Aliases for normalization
	FetchKeywordAliases() (map[string]string, error)
}
