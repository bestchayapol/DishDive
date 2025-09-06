package repository

import (
	"github.com/bestchayapol/DishDive/internal/entities"
	"gorm.io/gorm"
)

type recommendRepositoryDB struct {
	db *gorm.DB
}

func NewRecommendRepositoryDB(db *gorm.DB) RecommendRepository {
	return &recommendRepositoryDB{db: db}
}

// Get all user preferences and blacklist settings
func (r *recommendRepositoryDB) GetUserSettings(userID uint) ([]entities.PreferenceBlacklist, error) {
	var settings []entities.PreferenceBlacklist
	result := r.db.Where("user_id = ?", userID).Find(&settings)
	return settings, result.Error
}

// Get all keywords with user settings (includes unset keywords with default values)
func (r *recommendRepositoryDB) GetAllKeywordsWithUserSettings(userID uint) ([]entities.PreferenceBlacklist, error) {
	var result []entities.PreferenceBlacklist

	// Get all keywords and left join with user settings
	query := `
		SELECT 
			k.keyword_id,
			$1::integer as user_id,
			COALESCE(pb.preference, 0) as preference,
			COALESCE(pb.blacklist, 0) as blacklist
		FROM keywords k
		LEFT JOIN preference_blacklists pb ON k.keyword_id = pb.keyword_id AND pb.user_id = $2::integer
		ORDER BY k.category, k.keyword
	`

	err := r.db.Raw(query, userID, userID).Scan(&result).Error
	return result, err
}

// Bulk update user preferences and blacklist
func (r *recommendRepositoryDB) BulkUpdateUserSettings(userID uint, settings []entities.PreferenceBlacklist) error {
	// Use transaction for bulk upsert
	return r.db.Transaction(func(tx *gorm.DB) error {
		for _, setting := range settings {
			setting.UserID = userID
			
			// First, try to find existing record
			var existing entities.PreferenceBlacklist
			err := tx.Where("user_id = ? AND keyword_id = ?", setting.UserID, setting.KeywordID).
				First(&existing).Error
			
			if err == gorm.ErrRecordNotFound {
				// Record doesn't exist, create it
				if err := tx.Create(&setting).Error; err != nil {
					return err
				}
			} else if err != nil {
				// Some other database error occurred
				return err
			} else {
				// Record exists, update it using explicit WHERE conditions
				updateResult := tx.Model(&entities.PreferenceBlacklist{}).
					Where("user_id = ? AND keyword_id = ?", setting.UserID, setting.KeywordID).
					Updates(map[string]interface{}{
						"preference": setting.Preference,
						"blacklist":  setting.Blacklist,
					})
				if updateResult.Error != nil {
					return updateResult.Error
				}
			}
		}
		return nil
	})
}

// Reviews
func (r *recommendRepositoryDB) GetDishReviewPage(dishID uint) (*entities.Dish, *entities.Restaurant, error) {
	var dish entities.Dish
	if err := r.db.Where("dish_id = ?", dishID).First(&dish).Error; err != nil {
		return nil, nil, err
	}
	var restaurant entities.Restaurant
	if err := r.db.Where("res_id = ?", dish.ResID).First(&restaurant).Error; err != nil {
		return &dish, nil, err
	}
	return &dish, &restaurant, nil
}

func (r *recommendRepositoryDB) SubmitReview(userID uint, dishID uint, resID uint, reviewText string) error {
	review := entities.UserReview{
		UserID:  userID,
		DishID:  dishID,
		ResID:   resID,
		UserRev: reviewText,
	}
	return r.db.Create(&review).Error
}

// Get keyword by ID
func (r *recommendRepositoryDB) GetKeywordByID(keywordID uint) (entities.Keyword, error) {
	var kw entities.Keyword
	result := r.db.Where("keyword_id = ?", keywordID).First(&kw)
	return kw, result.Error
}

// Get keywords by category
func (r *recommendRepositoryDB) GetKeywordsByCategory(categories []string) ([]entities.Keyword, error) {
	var keywords []entities.Keyword
	result := r.db.Where("category IN ?", categories).Find(&keywords)
	return keywords, result.Error
}
