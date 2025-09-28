package service

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/entities"
	"github.com/bestchayapol/DishDive/internal/repository"
	"github.com/spf13/viper"
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

	// Define allowed keywords for restricted categories
	allowedFlavorKeywords := map[string]bool{
		"Sweet": true, "Salty": true, "Sour": true, "Spicy": true, "Oily": true,
	}
	allowedCostKeywords := map[string]bool{
		"Cheap": true, "Moderate": true, "Expensive": true,
	}

	var keywords []dtos.KeywordSettingResponse
	for _, setting := range settings {
		kw, err := s.recommendRepo.GetKeywordByID(setting.KeywordID)
		if err != nil {
			continue // Skip if keyword not found
		}

		// Filter based on category and keyword name
		shouldInclude := false
		switch kw.Category {
		case "system", "cuisine", "restriction":
			// Always include these categories
			shouldInclude = true
		case "flavor":
			// Only include specific flavor keywords
			shouldInclude = allowedFlavorKeywords[kw.Keyword]
		case "cost":
			// Only include specific cost keywords
			shouldInclude = allowedCostKeywords[kw.Keyword]
		default:
			// Don't include any other categories
			shouldInclude = false
		}

		if shouldInclude {
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
	}

	return dtos.UserSettingsResponse{Keywords: keywords}, nil
}

func (s *recommendService) UpdateUserSettings(userID uint, req dtos.BulkUpdateSettingsRequest) error {
	// Define allowed keywords for restricted categories
	allowedFlavorKeywords := map[string]bool{
		"Sweet": true, "Salty": true, "Sour": true, "Spicy": true, "Oily": true,
	}
	allowedCostKeywords := map[string]bool{
		"Cheap": true, "Moderate": true, "Expensive": true,
	}

	var settings []entities.PreferenceBlacklist
	for _, update := range req.Settings {
		// Get keyword details to check category and name
		kw, err := s.recommendRepo.GetKeywordByID(update.KeywordID)
		if err != nil {
			// Skip if keyword not found
			continue
		}

		// Filter based on category and keyword name
		shouldInclude := false
		switch kw.Category {
		case "system", "cuisine", "restriction":
			// Always include these categories
			shouldInclude = true
		case "flavor":
			// Only include specific flavor keywords
			shouldInclude = allowedFlavorKeywords[kw.Keyword]
		case "cost":
			// Only include specific cost keywords
			shouldInclude = allowedCostKeywords[kw.Keyword]
		default:
			// Don't include any other categories
			shouldInclude = false
		}

		if shouldInclude {
			settings = append(settings, entities.PreferenceBlacklist{
				UserID:     userID,
				KeywordID:  update.KeywordID,
				Preference: update.PreferenceValue,
				Blacklist:  update.BlacklistValue,
			})
		}
	}

	// If no valid settings, return success without doing anything
	if len(settings) == 0 {
		return nil
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
	// 1) Persist the user review and get its ID
	reviewID, err := s.recommendRepo.SubmitReview(req.UserID, req.DishID, req.ResID, req.ReviewText)
	if err != nil {
		return dtos.SubmitReviewResponse{Success: false}, err
	}

	// 2) Fire-and-forget: invoke Python single-review processor
	// We pass the restaurant name by looking up from Dish->Restaurant for better context
	var restaurantName string
	if dish, derr := s.foodRepo.GetDishByID(req.DishID); derr == nil {
		if res, rerr := s.foodRepo.GetRestaurantByID(dish.ResID); rerr == nil {
			restaurantName = res.ResName
		}
	}
	if restaurantName == "" {
		restaurantName = ""
	}

	// Construct command: python -m llm_processing.single_review ...
	// Allow override via PYTHON_EXEC, default to "python"
	pyExec := os.Getenv("PYTHON_EXEC")
	if pyExec == "" {
		pyExec = "python"
	}
	cmd := exec.Command(pyExec, "-m", "llm_processing.single_review",
		"--restaurant", restaurantName,
		"--review", req.ReviewText,
		"--source-id", fmt.Sprintf("%d", reviewID),
		"--source-type", "user",
	)

	// Propagate DB env and any OpenAI settings from the host environment
	env := os.Environ()
	appendIfNotEmpty := func(k string) {
		if v := os.Getenv(k); v != "" {
			env = append(env, fmt.Sprintf("%s=%s", k, v))
		}
	}
	for _, k := range []string{
		"PG_HOST", "PG_PORT", "PG_USER", "PG_PASSWORD", "PG_DATABASE", "PG_SSLMODE",
		"OPENAI_API_KEY", "OPENAI_MODEL",
		"LOG_LEVEL",
	} {
		appendIfNotEmpty(k)
	}
	// Ensure PYTHONPATH includes the project root (parent of server dir) so module imports work
	if wd, _ := os.Getwd(); wd != "" {
		projectRoot := filepath.Dir(wd)
		existing := os.Getenv("PYTHONPATH")
		sep := string(os.PathListSeparator)
		if existing != "" {
			env = append(env, fmt.Sprintf("PYTHONPATH=%s%s%s", existing, sep, projectRoot))
		} else {
			env = append(env, fmt.Sprintf("PYTHONPATH=%s", projectRoot))
		}
		// Also set working directory for the subprocess to the project root
		cmd.Dir = projectRoot
	}
	// If DB envs are not present, fill from viper config so Python gets the same DB
	if os.Getenv("PG_HOST") == "" {
		env = append(env, fmt.Sprintf("%s=%s", "PG_HOST", viper.GetString("db.host")))
	}
	if os.Getenv("PG_PORT") == "" {
		env = append(env, fmt.Sprintf("%s=%d", "PG_PORT", viper.GetInt("db.port")))
	}
	if os.Getenv("PG_USER") == "" {
		env = append(env, fmt.Sprintf("%s=%s", "PG_USER", viper.GetString("db.username")))
	}
	if os.Getenv("PG_PASSWORD") == "" {
		env = append(env, fmt.Sprintf("%s=%s", "PG_PASSWORD", viper.GetString("db.password")))
	}
	if os.Getenv("PG_DATABASE") == "" {
		env = append(env, fmt.Sprintf("%s=%s", "PG_DATABASE", viper.GetString("db.database")))
	}

	// Ensure DB writes are enabled for this run and disable CSV side outputs by default
	env = append(env, "PG_WRITE_DISABLED=0")
	if os.Getenv("WRITE_CHECKPOINT") == "" {
		env = append(env, "WRITE_CHECKPOINT=0")
	}
	if os.Getenv("WRITE_DATA_EXTRACT") == "" {
		env = append(env, "WRITE_DATA_EXTRACT=0")
	}
	cmd.Env = env

	// Start without waiting; log stderr if it fails to start
	if err := cmd.Start(); err != nil {
		fmt.Printf("[llm] failed to start single_review processor: %v\n", err)
	} else {
		go func() {
			// Wait in a goroutine so the process can finish in background
			if werr := cmd.Wait(); werr != nil {
				fmt.Printf("[llm] processor exited with error: %v\n", werr)
			}
		}()
	}

	return dtos.SubmitReviewResponse{Success: true, ReviewID: &reviewID}, nil
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
	var sentimentPreference float64 = 0
	var sentimentBlacklist float64 = 0
	
	for _, setting := range userSettings {
		if setting.Preference > 0 {
			// Check if it's sentiment keyword
			kw, err := s.recommendRepo.GetKeywordByID(setting.KeywordID)
			if err == nil && kw.Category == "system" && kw.Keyword == "sentiment" {
				sentimentPreference = setting.Preference
			} else {
				preferenceMap[setting.KeywordID] = setting.Preference
			}
		}
		if setting.Blacklist > 0 {
			// Check if it's sentiment keyword
			kw, err := s.recommendRepo.GetKeywordByID(setting.KeywordID)
			if err == nil && kw.Category == "system" && kw.Keyword == "sentiment" {
				sentimentBlacklist = setting.Blacklist
			} else {
				blacklistMap[setting.KeywordID] = setting.Blacklist
			}
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
		sentiment float64
	}

	var scoredDishes []scoredDish
	for _, dish := range dishes {
		// Calculate sentiment percentage using proper review counts
		positiveReviews, totalReviews, err := s.foodRepo.GetReviewCountsByDish(dish.DishID)
		if err != nil {
			positiveReviews, totalReviews = 0, 0
		}
		
		var sentimentPercentage float64 = 0
		if totalReviews > 0 {
			sentimentPercentage = float64(positiveReviews) / float64(totalReviews) * 100
		}

		// Start with sentiment as base score
		score := sentimentPercentage
		isFav := favoriteMap[dish.DishID]
		shouldSkip := false

		// Get dish keywords and apply preference/blacklist logic
		keywords, _ := s.foodRepo.GetKeywordsByDish(dish.DishID)

		// Debug log: Keywords fetched for the dish
		fmt.Printf("DishID: %d, Keywords: %v\n", dish.DishID, keywords)

		// First check blacklist - if ANY keyword is blacklisted, skip dish entirely
		for _, kw := range keywords {
			if _, exists := blacklistMap[kw.KeywordID]; exists {
				shouldSkip = true
				break
			}
		}

		// Check sentiment blacklist
		if sentimentBlacklist > 0 && sentimentPercentage < (sentimentBlacklist * 100) {
			shouldSkip = true
		}

		// Skip blacklisted dishes entirely
		if shouldSkip {
			continue
		}

		// Apply preference boosts (+10 per preferred keyword)
		for _, kw := range keywords {
			if _, exists := preferenceMap[kw.KeywordID]; exists {
				score += 20
				// Debug log: Preference boost applied
				fmt.Printf("DishID: %d, Keyword: %s, Boost: +10\n", dish.DishID, kw.Keyword)
			}
		}

		// Apply sentiment preference boost
		if sentimentPreference > 0 && sentimentPercentage > (sentimentPreference * 100) {
			score += 20
		}

		// Favorites boost (x3)
		if isFav {
			score *= 3.0
		}

		// Debug log: Final score for the dish
		// fmt.Printf("DishID: %d, Final Score: %.2f\n", dish.DishID, score)

		scoredDishes = append(scoredDishes, scoredDish{
			dish: dish, 
			score: score, 
			isFav: isFav,
			sentiment: sentimentPercentage,
		})
	}

	// 5. Sort by recommendation score (highest first)
	sort.Slice(scoredDishes, func(i, j int) bool {
		return scoredDishes[i].score > scoredDishes[j].score
	})

	// 6. Build response
	var resp []dtos.RestaurantMenuItemResponse
	for _, sd := range scoredDishes {
		// Get cuisine image
		var imageLink *string
		if sd.dish.Cuisine != nil {
			imageURL, err := s.foodRepo.GetCuisineImageByCuisine(*sd.dish.Cuisine)
			if err == nil && imageURL != "" {
				imageLink = &imageURL
			}
		}

		// Get prominent flavor
		prominentFlavor, err := s.foodRepo.GetProminentFlavorByDish(sd.dish.DishID)
		if err != nil {
			prominentFlavor = nil
		}

		// Get review counts for response
		positiveReviews, totalReviews, err := s.foodRepo.GetReviewCountsByDish(sd.dish.DishID)
		if err != nil {
			positiveReviews, totalReviews = 0, 0
		}

		resp = append(resp, dtos.RestaurantMenuItemResponse{
			DishID:          sd.dish.DishID,
			DishName:        sd.dish.DishName,
			ImageLink:       imageLink,
			SentimentScore:  sd.sentiment,
			PositiveReviews: positiveReviews,
			TotalReviews:    totalReviews,
			Cuisine:         sd.dish.Cuisine,
			ProminentFlavor: prominentFlavor,
			IsFavorite:      sd.isFav,
			RecommendScore:  sd.score,
		})
	}

	return resp, nil
}

func (s *recommendService) HasReviewExtract(sourceID uint, sourceType string) (bool, error) {
	return s.recommendRepo.HasReviewExtract(sourceID, sourceType)
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
