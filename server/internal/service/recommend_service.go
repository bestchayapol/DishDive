package service

import (
	"sort"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/entities"
	"github.com/bestchayapol/DishDive/internal/repository"
)

type recommendService struct {
	foodRepo      repository.FoodRepository
	recommendRepo repository.RecommendRepository
}

func NewRecommendService(foodRepo repository.FoodRepository, recommendRepo repository.RecommendRepository) RecommendService {
	return &recommendService{foodRepo: foodRepo, recommendRepo: recommendRepo}
}

// New unified settings methods
func (s *recommendService) GetUserSettings(userID uint) (dtos.UserSettingsResponse, error) {
	settings, err := s.recommendRepo.GetAllKeywordsWithUserSettings(userID)
	if err != nil {
		return dtos.UserSettingsResponse{}, err
	}

	var keywords []dtos.KeywordSettingResponse
	for _, setting := range settings {
		kw, err := s.recommendRepo.GetKeywordByID(setting.KeywordID)
		if err != nil {
			continue // Skip if keyword not found
		}

		keywords = append(keywords, dtos.KeywordSettingResponse{
			KeywordID:       setting.KeywordID,
			Keyword:         kw.Keyword,
			Category:        kw.Category,
			PreferenceValue: setting.Preference,
			BlacklistValue:  setting.Blacklist,
			IsPreferred:     setting.Preference > 0,
			IsBlacklisted:   setting.Blacklist > 0,
		})
	}

	return dtos.UserSettingsResponse{Keywords: keywords}, nil
}

func (s *recommendService) UpdateUserSettings(userID uint, req dtos.BulkUpdateSettingsRequest) error {
	var settings []entities.PreferenceBlacklist
	for _, update := range req.Settings {
		settings = append(settings, entities.PreferenceBlacklist{
			UserID:     userID,
			KeywordID:  update.KeywordID,
			Preference: update.PreferenceValue,
			Blacklist:  update.BlacklistValue,
		})
	}
	return s.recommendRepo.BulkUpdateUserSettings(userID, settings)
}

func (s *recommendService) GetDishReviewPage(dishID uint) (dtos.DishReviewPageResponse, error) {
	dish, err := s.foodRepo.GetDishByID(dishID)
	if err != nil {
		return dtos.DishReviewPageResponse{}, err
	}
	res, err := s.foodRepo.GetRestaurantByID(dish.ResID)
	if err != nil {
		return dtos.DishReviewPageResponse{}, err
	}
	return dtos.DishReviewPageResponse{
		DishID:    dish.DishID,
		DishName:  dish.DishName,
		ImageLink: getCuisineImageLink(s.foodRepo, dish.Cuisine),
		ResID:     res.ResID,
		ResName:   res.ResName,
	}, nil
}

func (s *recommendService) SubmitReview(req dtos.SubmitReviewRequest) (dtos.SubmitReviewResponse, error) {
	err := s.recommendRepo.SubmitReview(req.UserID, req.DishID, req.ResID, req.ReviewText)
	return dtos.SubmitReviewResponse{Success: err == nil}, err
}

func (s *recommendService) GetRecommendedDishes(userID uint, resID *uint) ([]dtos.RestaurantMenuItemResponse, error) {
	// 1. Get dishes - either from specific restaurant or all dishes
	var dishes []entities.Dish
	var err error
	if resID != nil {
		dishes, err = s.foodRepo.GetDishesByRestaurant(*resID)
	} else {
		dishes, err = s.foodRepo.GetAllDishes()
	}
	if err != nil {
		return nil, err
	}

	// 2. Get user settings (unified approach)
	userSettings, err := s.recommendRepo.GetUserSettings(userID)
	if err != nil {
		userSettings = []entities.PreferenceBlacklist{} // Continue with empty settings if error
	}

	// Create maps for quick lookup
	preferenceMap := make(map[uint]float64)
	blacklistMap := make(map[uint]float64)
	for _, setting := range userSettings {
		if setting.Preference > 0 {
			preferenceMap[setting.KeywordID] = setting.Preference
		}
		if setting.Blacklist > 0 {
			blacklistMap[setting.KeywordID] = setting.Blacklist
		}
	}

	// 3. Get user's favorites
	favoriteDishes, _ := s.foodRepo.GetFavoriteDishesByUser(userID)
	favoriteMap := make(map[uint]bool)
	for _, fav := range favoriteDishes {
		favoriteMap[fav.DishID] = true
	}

	// 4. Calculate scores for each dish
	type scoredDish struct {
		dish  entities.Dish
		score float64
		isFav bool
	}

	var scoredDishes []scoredDish
	for _, dish := range dishes {
		score := dish.TotalScore
		isFav := favoriteMap[dish.DishID]
		isBlacklisted := false

		// Get dish keywords and apply preference/blacklist logic
		keywords, _ := s.foodRepo.GetKeywordsByDish(dish.DishID)
		for _, kw := range keywords {
			// Apply blacklist first (if any keyword is blacklisted, skip dish)
			if threshold, exists := blacklistMap[kw.KeywordID]; exists {
				if dish.TotalScore <= threshold {
					isBlacklisted = true
					break
				}
			}
		}

		// Skip blacklisted dishes entirely
		if isBlacklisted {
			continue
		}

		// Apply preferences
		for _, kw := range keywords {
			if threshold, exists := preferenceMap[kw.KeywordID]; exists {
				if dish.TotalScore >= threshold {
					score += 10 // Boost score for preferred keywords above threshold
				}
			}
		}

		// Favorites boost
		if isFav {
			score *= 1.5
		}

		scoredDishes = append(scoredDishes, scoredDish{dish: dish, score: score, isFav: isFav})
	}

	// 5. Sort by recommendation score
	sort.Slice(scoredDishes, func(i, j int) bool {
		return scoredDishes[i].score > scoredDishes[j].score
	})

	// 6. Build response
	var resp []dtos.RestaurantMenuItemResponse
	for _, sd := range scoredDishes {
		// Calculate percentage score for display
		var percentage float64
		if sd.dish.PositiveScore+sd.dish.NegativeScore > 0 {
			percentage = float64(sd.dish.PositiveScore) / float64(sd.dish.PositiveScore+sd.dish.NegativeScore) * 100
		}

		resp = append(resp, dtos.RestaurantMenuItemResponse{
			DishID:          sd.dish.DishID,
			DishName:        sd.dish.DishName,
			ImageLink:       getCuisineImageLink(s.foodRepo, sd.dish.Cuisine),
			SentimentScore:  percentage,
			Cuisine:         sd.dish.Cuisine,
			ProminentFlavor: nil, // Fill as needed
			IsFavorite:      sd.isFav,
			RecommendScore:  sd.score,
		})
	}

	return resp, nil
}

// Helper function to get cuisine image link
func getCuisineImageLink(foodRepo repository.FoodRepository, cuisine *string) *string {
	if cuisine == nil {
		return nil
	}

	imageURL, err := foodRepo.GetCuisineImageByCuisine(*cuisine)
	if err != nil || imageURL == "" {
		return nil
	}

	return &imageURL
}
