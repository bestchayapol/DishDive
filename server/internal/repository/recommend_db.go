package repository

import (
	"strings"

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

func (r *recommendRepositoryDB) SubmitReview(userID uint, dishID uint, resID uint, reviewText string) (uint, error) {
	review := entities.UserReview{
		UserID:  userID,
		DishID:  dishID,
		ResID:   resID,
		UserRev: reviewText,
	}
	if err := r.db.Create(&review).Error; err != nil {
		return 0, err
	}
	return review.UserRevID, nil
}

func (r *recommendRepositoryDB) HasReviewExtract(sourceID uint, sourceType string) (bool, error) {
	var count int64
	err := r.db.Table("review_extracts").Where("source_id = ? AND source_type = ?", sourceID, sourceType).Count(&count).Error
	return count > 0, err
}

func (r *recommendRepositoryDB) HasNormalizedReview(sourceID uint) (bool, error) {
	var count int64
	err := r.db.Table("review_dishes").Where("source_id = ?", sourceID).Count(&count).Error
	return count > 0, err
}

// UpsertReviewExtract writes or updates an extraction result for a given (source_type, source_id)
func (r *recommendRepositoryDB) UpsertReviewExtract(sourceID uint, sourceType string, dataExtract string) error {
	// Try to find existing record first
	var existing entities.ReviewExtract
	err := r.db.Where("source_id = ? AND source_type = ?", sourceID, sourceType).First(&existing).Error

	if err == gorm.ErrRecordNotFound {
		// Create new record
		rec := entities.ReviewExtract{
			SourceID:    sourceID,
			SourceType:  sourceType,
			DataExtract: dataExtract,
		}
		return r.db.Create(&rec).Error
	} else if err != nil {
		return err
	} else {
		// Update existing record
		return r.db.Model(&existing).Update("data_extract", dataExtract).Error
	}
}

func (r *recommendRepositoryDB) GetLatestReviewExtract(sourceID uint, sourceType string) (string, error) {
	var rec entities.ReviewExtract
	if err := r.db.Where("source_id = ? AND source_type = ?", sourceID, sourceType).Order("rev_ext_id DESC").First(&rec).Error; err != nil {
		return "", err
	}
	return rec.DataExtract, nil
}

// EnsureReviewDish creates a review_dishes row if missing and returns it
func (r *recommendRepositoryDB) EnsureReviewDish(sourceID uint, dishID uint, resID uint) (*entities.ReviewDish, error) {
	// Try to find existing
	var rd entities.ReviewDish
	if err := r.db.Where("source_id = ? AND dish_id = ? AND res_id = ?", sourceID, dishID, resID).First(&rd).Error; err == nil {
		return &rd, nil
	}
	rd = entities.ReviewDish{SourceID: sourceID, DishID: dishID, ResID: resID}
	if err := r.db.Create(&rd).Error; err != nil {
		return nil, err
	}
	return &rd, nil
}

// FindKeywordByName resolves a keyword by its exact text; returns nil if not found
func (r *recommendRepositoryDB) FindKeywordByName(name string) (*entities.Keyword, error) {
	var kw entities.Keyword
	if err := r.db.Where("keyword = ?", name).First(&kw).Error; err != nil {
		return nil, err
	}
	return &kw, nil
}

// EnsureReviewDishKeyword ensures the link row exists
func (r *recommendRepositoryDB) EnsureReviewDishKeyword(reviewDishID uint, keywordID uint) error {
	var rdk entities.ReviewDishKeyword
	if err := r.db.Where("review_dish_id = ? AND keyword_id = ?", reviewDishID, keywordID).First(&rdk).Error; err == nil {
		return nil
	}
	rdk = entities.ReviewDishKeyword{RDID: reviewDishID, KeywordID: keywordID}
	return r.db.Create(&rdk).Error
}

// FindOrCreateKeyword by name/category/sentiment
func (r *recommendRepositoryDB) FindOrCreateKeyword(name string, category string, sentiment string) (*entities.Keyword, error) {
	var kw entities.Keyword
	if err := r.db.Where("keyword = ? AND category = ? AND sentiment = ?", name, category, sentiment).First(&kw).Error; err == nil {
		return &kw, nil
	}
	kw = entities.Keyword{Keyword: name, Category: category, Sentiment: sentiment}
	if err := r.db.Create(&kw).Error; err != nil {
		return nil, err
	}
	return &kw, nil
}

// BumpDishKeyword increments dish_keywords.frequency, creating the row if needed
func (r *recommendRepositoryDB) BumpDishKeyword(dishID uint, keywordID uint, delta int) error {
	// Try update
	res := r.db.Model(&entities.DishKeyword{}).
		Where("dish_id = ? AND keyword_id = ?", dishID, keywordID).
		UpdateColumn("frequency", gorm.Expr("COALESCE(frequency,0) + ?", delta))
	if res.Error == nil && res.RowsAffected > 0 {
		return nil
	}
	// Create if missing
	dk := entities.DishKeyword{DishID: dishID, KeywordID: keywordID, Frequency: uint(delta)}
	return r.db.Create(&dk).Error
}

// RecomputeScoresAndRestaurants mirrors the Python SQL updates
func (r *recommendRepositoryDB) RecomputeScoresAndRestaurants() error {
	// Positive/Negative per review aggregation -> update dishes
	if err := r.db.Exec(`
		WITH per_review AS (
			SELECT rd.dish_id, rd.review_dish_id,
				   MAX(CASE WHEN k.sentiment = 'positive' THEN 1 ELSE 0 END) AS has_pos,
				   MAX(CASE WHEN k.sentiment = 'negative' THEN 1 ELSE 0 END) AS has_neg
			FROM review_dishes rd
			LEFT JOIN review_dish_keywords rdk ON rdk.review_dish_id = rd.review_dish_id
			LEFT JOIN keywords k ON k.keyword_id = rdk.keyword_id
			GROUP BY rd.dish_id, rd.review_dish_id
		), agg AS (
			SELECT dish_id,
				   SUM(has_pos) AS pos,
				   SUM(has_neg) AS neg,
				   COUNT(*)      AS total_reviews
			FROM per_review
			GROUP BY dish_id
		)
		UPDATE dishes d
		SET positive_score = COALESCE(a.pos, 0),
			negative_score = COALESCE(a.neg, 0),
			total_score    = COALESCE(a.total_reviews, 0)
		FROM agg a
		WHERE a.dish_id = d.dish_id`).Error; err != nil {
		return err
	}
	// Update restaurant menu_size
	if err := r.db.Exec(`
		UPDATE restaurants r SET menu_size=COALESCE(s.cnt,0)
		FROM (SELECT res_id, COUNT(*) AS cnt FROM dishes GROUP BY res_id) s
		WHERE s.res_id=r.res_id`).Error; err != nil {
		return err
	}
	// Majority cuisine (>=80%)
	if err := r.db.Exec(`
		WITH per_res AS (
			SELECT res_id, cuisine, COUNT(*) AS cnt,
				   SUM(COUNT(*)) OVER (PARTITION BY res_id) AS total
			FROM dishes
			WHERE cuisine IS NOT NULL AND cuisine <> ''
			GROUP BY res_id, cuisine
		), pick AS (
			SELECT res_id, cuisine, cnt, total,
				   ROW_NUMBER() OVER (PARTITION BY res_id ORDER BY cnt DESC) AS rn
			FROM per_res
		)
		UPDATE restaurants r
		SET res_cuisine = CASE WHEN p.cnt >= 0.8 * p.total THEN p.cuisine ELSE NULL END
		FROM pick p
		WHERE p.res_id = r.res_id AND p.rn = 1`).Error; err != nil {
		return err
	}
	// Majority restriction (>=80%)
	if err := r.db.Exec(`
		WITH per_res AS (
			SELECT res_id, restriction, COUNT(*) AS cnt,
				   SUM(COUNT(*)) OVER (PARTITION BY res_id) AS total
			FROM dishes
			WHERE restriction IS NOT NULL AND restriction <> ''
			GROUP BY res_id, restriction
		), pick AS (
			SELECT res_id, restriction, cnt, total,
				   ROW_NUMBER() OVER (PARTITION BY res_id ORDER BY cnt DESC) AS rn
			FROM per_res
		)
		UPDATE restaurants r
		SET res_restriction = CASE WHEN p.cnt >= 0.8 * p.total THEN p.restriction ELSE NULL END
		FROM pick p
		WHERE p.res_id = r.res_id AND p.rn = 1`).Error; err != nil {
		return err
	}
	return nil
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

// FetchKeywordAliases loads all alt_word -> base keyword mappings
func (r *recommendRepositoryDB) FetchKeywordAliases() (map[string]string, error) {
	rows := []struct {
		AltWord string
		Keyword string
	}{}
	err := r.db.Table("keyword_aliases ka").
		Select("ka.alt_word as alt_word, k.keyword as keyword").
		Joins("JOIN keywords k ON k.keyword_id = ka.keyword_id").
		Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	m := make(map[string]string, len(rows))
	for _, r := range rows {
		m[strings.ToLower(strings.TrimSpace(r.AltWord))] = r.Keyword
	}
	return m, nil
}
