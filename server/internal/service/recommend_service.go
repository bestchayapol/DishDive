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

func (s *recommendService) GetPreferenceKeywords(userID uint) ([]dtos.PreferenceKeywordResponse, error) {
	prefs, err := s.recommendRepo.GetPreferencesByUser(userID)
	if err != nil {
		return nil, err
	}
	var resp []dtos.PreferenceKeywordResponse
	for _, p := range prefs {
		kw, err := s.recommendRepo.GetKeywordByID(p.KeywordID)
		keyword := ""
		category := ""
		if err == nil {
			keyword = kw.Keyword
			category = kw.Category
		}
		resp = append(resp, dtos.PreferenceKeywordResponse{
			KeywordID:          p.KeywordID,
			Keyword:            keyword,
			Category:           category,
			IsPreferred:        p.Preference > 0,
			SentimentThreshold: p.Preference,
		})
	}
	return resp, nil
}

func (s *recommendService) SetPreference(userID uint, req dtos.SetPreferenceRequest) error {
	return s.recommendRepo.SetPreference(userID, req.KeywordID, req.SentimentThreshold)
}

func (s *recommendService) GetBlacklistKeywords(userID uint) ([]dtos.BlacklistKeywordResponse, error) {
	bls, err := s.recommendRepo.GetBlacklistByUser(userID)
	if err != nil {
		return nil, err
	}
	var resp []dtos.BlacklistKeywordResponse
	for _, b := range bls {
		kw, err := s.recommendRepo.GetKeywordByID(b.KeywordID)
		keyword := ""
		category := ""
		if err == nil {
			keyword = kw.Keyword
			category = kw.Category
		}
		resp = append(resp, dtos.BlacklistKeywordResponse{
			KeywordID:          b.KeywordID,
			Keyword:            keyword,
			Category:           category,
			IsBlacklisted:      b.Blacklist > 0,
			SentimentThreshold: b.Blacklist,
		})
	}
	return resp, nil
}

func (s *recommendService) SetBlacklist(userID uint, req dtos.SetBlacklistRequest) error {
	return s.recommendRepo.SetBlacklist(userID, req.KeywordID, req.SentimentThreshold)
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
		ImageLink: nil,
		ResID:     res.ResID,
		ResName:   res.ResName,
	}, nil
}

func (s *recommendService) SubmitReview(req dtos.SubmitReviewRequest) (dtos.SubmitReviewResponse, error) {
	err := s.recommendRepo.SubmitReview(req.UserID, req.DishID, req.ResID, req.ReviewText)
	return dtos.SubmitReviewResponse{Success: err == nil}, err
}

func (s *recommendService) GetRecommendedDishes(userID uint) ([]dtos.FavoriteDishResponse, error) {
	// 1. Get all dishes sorted by sentiment score
	dishes, err := s.foodRepo.GetAllDishes()
	if err != nil {
		return nil, err
	}
	// 2. Get user preferences and blacklist
	preferredKeywords, _ := s.recommendRepo.GetPreferencesByUser(userID)
	blacklistedKeywords, _ := s.recommendRepo.GetBlacklistByUser(userID)
	// 3. Get user's favorites
	favoriteDishes, _ := s.foodRepo.GetFavoriteDishesByUser(userID)
	favoriteMap := make(map[uint]bool)
	for _, fav := range favoriteDishes {
		favoriteMap[fav.DishID] = true
	}
	// 4. Get dish-keyword mappings
	// For simplicity, assume a method GetKeywordsByDish(dishID uint) ([]entities.Keyword, error) exists in foodRepo
	type scoredDish struct {
		dish  entities.Dish
		score float64
	}
	var scoredDishes []scoredDish
	for _, dish := range dishes {
		score := dish.TotalScore
		// Check keywords
		keywords, _ := s.foodRepo.GetKeywordsByDish(dish.DishID)
		for _, kw := range keywords {
			for _, pref := range preferredKeywords {
				if kw.KeywordID == pref.KeywordID {
					score += 10
				}
			}
			for _, bl := range blacklistedKeywords {
				if kw.KeywordID == bl.KeywordID {
					score = 0
				}
			}
		}
		// Sentiment score settings (using preference/blacklist thresholds)
		for _, pref := range preferredKeywords {
			if dish.TotalScore > pref.Preference {
				score += 10
			}
		}
		for _, bl := range blacklistedKeywords {
			if dish.TotalScore < bl.Blacklist {
				score = 0
			}
		}
		// Favorites boost
		if favoriteMap[dish.DishID] {
			score *= 2
		}
		scoredDishes = append(scoredDishes, scoredDish{dish: dish, score: score})
	}
	// 5. Sort by score
	sort.Slice(scoredDishes, func(i, j int) bool {
		return scoredDishes[i].score > scoredDishes[j].score
	})
	// 6. Build response
	var resp []dtos.FavoriteDishResponse
	for _, sd := range scoredDishes {
		resp = append(resp, dtos.FavoriteDishResponse{
			DishID:          sd.dish.DishID,
			DishName:        sd.dish.DishName,
			ImageLink:       nil, // Fill as needed
			SentimentScore:  sd.dish.TotalScore,
			Cuisine:         sd.dish.Cuisine,
			ProminentFlavor: nil, // Fill as needed
		})
	}
	return resp, nil
}
