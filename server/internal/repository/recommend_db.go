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

// Get preferences for a user (with sentiment threshold)
func (r *recommendRepositoryDB) GetPreferencesByUser(userID uint) ([]entities.PreferenceBlacklist, error) {
	var prefs []entities.PreferenceBlacklist
	result := r.db.Where("user_id = ? AND preference > 0", userID).Find(&prefs)
	return prefs, result.Error
}

// Set preference for a keyword
func (r *recommendRepositoryDB) SetPreference(userID, keywordID uint, threshold float64) error {
	pref := entities.PreferenceBlacklist{UserID: userID, KeywordID: keywordID, Preference: threshold}
	return r.db.Save(&pref).Error
}

// Get blacklist for a user (with sentiment threshold)
func (r *recommendRepositoryDB) GetBlacklistByUser(userID uint) ([]entities.PreferenceBlacklist, error) {
	var bls []entities.PreferenceBlacklist
	result := r.db.Where("user_id = ? AND blacklist > 0", userID).Find(&bls)
	return bls, result.Error
}

// Set blacklist for a keyword
func (r *recommendRepositoryDB) SetBlacklist(userID, keywordID uint, threshold float64) error {
	bl := entities.PreferenceBlacklist{UserID: userID, KeywordID: keywordID, Blacklist: threshold}
	return r.db.Save(&bl).Error
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
