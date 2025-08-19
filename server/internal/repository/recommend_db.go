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

// Preference/Blacklist
func (r *recommendRepositoryDB) GetPreferenceKeywordsByUser(userID uint) ([]entities.Keyword, error) {
    var keywords []entities.Keyword
    r.db.Joins("JOIN preference_blacklist ON preference_blacklist.keyword_id = keyword.keyword_id").
        Where("preference_blacklist.user_id = ? AND preference_blacklist.preference IS NOT NULL", userID).
        Find(&keywords)
    return keywords, nil
}

func (r *recommendRepositoryDB) SetPreferenceForKeyword(userID uint, keywordID uint, isPreferred bool, sentimentThreshold float64) error {
    pref := entities.PreferenceBlacklist{
        UserID: userID,
        KeywordID: keywordID,
        Preference: func() float64 { if isPreferred { return sentimentThreshold } else { return 0 } }(),
    }
    return r.db.Save(&pref).Error
}

func (r *recommendRepositoryDB) GetBlacklistKeywordsByUser(userID uint) ([]entities.Keyword, error) {
    var keywords []entities.Keyword
    r.db.Joins("JOIN preference_blacklist ON preference_blacklist.keyword_id = keyword.keyword_id").
        Where("preference_blacklist.user_id = ? AND preference_blacklist.blacklist IS NOT NULL", userID).
        Find(&keywords)
    return keywords, nil
}

func (r *recommendRepositoryDB) SetBlacklistForKeyword(userID uint, keywordID uint, isBlacklisted bool, sentimentThreshold float64) error {
    bl := entities.PreferenceBlacklist{
        UserID: userID,
        KeywordID: keywordID,
        Blacklist: func() float64 { if isBlacklisted { return sentimentThreshold } else { return 0 } }(),
    }
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
        UserID: userID,
        DishID: dishID,
        ResID: resID,
        UserRev: reviewText,
    }
    return r.db.Create(&review).Error
}