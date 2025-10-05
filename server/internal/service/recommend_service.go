package service

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/entities"
	"github.com/bestchayapol/DishDive/internal/repository"
	"github.com/spf13/viper"
)

type recommendService struct {
	foodRepo      repository.FoodRepository
	recommendRepo repository.RecommendRepository
	// mapping caches
	flavorENToIDs map[string]map[uint]struct{}
	costENToIDs   map[string]map[uint]struct{}
}

func NewRecommendService(foodRepo repository.FoodRepository, recommendRepo repository.RecommendRepository) RecommendService {
	rs := &recommendService{foodRepo: foodRepo, recommendRepo: recommendRepo}
	rs.loadKeywordMapping()
	return rs
}

// keywordMappingFile structure
type keywordMapping struct {
	Flavor map[string][]string `json:"flavor"`
	Cost   map[string][]string `json:"cost"`
}

func (s *recommendService) loadKeywordMapping() {
	// Default path: ./config/keyword_mapping.json (relative to server working dir)
	mappingPath := filepath.Join("config", "keyword_mapping.json")
	// Allow override via env
	if p := os.Getenv("KEYWORD_MAPPING_PATH"); p != "" {
		mappingPath = p
	}
	f, err := os.Open(mappingPath)
	if err != nil {
		fmt.Printf("[mapping] no mapping file found at %s: %v\n", mappingPath, err)
		s.flavorENToIDs = map[string]map[uint]struct{}{}
		s.costENToIDs = map[string]map[uint]struct{}{}
		return
	}
	defer f.Close()
	var m keywordMapping
	if err := json.NewDecoder(f).Decode(&m); err != nil {
		fmt.Printf("[mapping] failed to parse mapping json: %v\n", err)
		s.flavorENToIDs = map[string]map[uint]struct{}{}
		s.costENToIDs = map[string]map[uint]struct{}{}
		return
	}
	// Resolve Thai strings to keyword_ids by category
	keywords, kerr := s.recommendRepo.GetKeywordsByCategory([]string{"flavor", "cost"})
	if kerr != nil {
		fmt.Printf("[mapping] failed to load keywords: %v\n", kerr)
		return
	}
	// Build lookup: category -> thai word -> id
	type key struct{ cat, name string }
	thaiToID := map[key]uint{}
	for _, kw := range keywords {
		thaiToID[key{kw.Category, kw.Keyword}] = kw.KeywordID
	}
	s.flavorENToIDs = map[string]map[uint]struct{}{}
	s.costENToIDs = map[string]map[uint]struct{}{}
	// Helper to add
	addSet := func(dst map[string]map[uint]struct{}, en string, id uint) {
		if dst[en] == nil {
			dst[en] = map[uint]struct{}{}
		}
		dst[en][id] = struct{}{}
	}
	for en, list := range m.Flavor {
		for _, thai := range list {
			if id, ok := thaiToID[key{"flavor", thai}]; ok {
				addSet(s.flavorENToIDs, en, id)
			}
		}
	}
	for en, list := range m.Cost {
		for _, thai := range list {
			if id, ok := thaiToID[key{"cost", thai}]; ok {
				addSet(s.costENToIDs, en, id)
			}
		}
	}
	// Log coverage
	fmt.Printf("[mapping] loaded flavor groups=%d, cost groups=%d\n", len(s.flavorENToIDs), len(s.costENToIDs))
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
	// Build reverse maps id->english option membership
	revFlavor := map[uint][]string{}
	revCost := map[uint][]string{}
	for en, ids := range s.flavorENToIDs {
		for id := range ids {
			revFlavor[id] = append(revFlavor[id], en)
		}
	}
	for en, ids := range s.costENToIDs {
		for id := range ids {
			revCost[id] = append(revCost[id], en)
		}
	}
	// Track selected english options for both preferred and blacklisted
	prefFlavorEN := map[string]struct{}{}
	prefCostEN := map[string]struct{}{}
	blackFlavorEN := map[string]struct{}{}
	blackCostEN := map[string]struct{}{}
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
			// Collect normalized selections
			if kw.Category == "flavor" {
				if setting.Preference > 0 {
					for _, en := range revFlavor[setting.KeywordID] {
						prefFlavorEN[en] = struct{}{}
					}
				}
				if setting.Blacklist > 0 {
					for _, en := range revFlavor[setting.KeywordID] {
						blackFlavorEN[en] = struct{}{}
					}
				}
			} else if kw.Category == "cost" {
				if setting.Preference > 0 {
					for _, en := range revCost[setting.KeywordID] {
						prefCostEN[en] = struct{}{}
					}
				}
				if setting.Blacklist > 0 {
					for _, en := range revCost[setting.KeywordID] {
						blackCostEN[en] = struct{}{}
					}
				}
			}
		}
	}
	// Convert sets to slices (stable order)
	toSlice := func(m map[string]struct{}) []string {
		out := make([]string, 0, len(m))
		for k := range m {
			out = append(out, k)
		}
		sort.Strings(out)
		return out
	}
	return dtos.UserSettingsResponse{
		Keywords:            keywords,
		FlavorENPreferred:   toSlice(prefFlavorEN),
		CostENPreferred:     toSlice(prefCostEN),
		FlavorENBlacklisted: toSlice(blackFlavorEN),
		CostENBlacklisted:   toSlice(blackCostEN),
	}, nil
}

func (s *recommendService) UpdateUserSettings(userID uint, req dtos.BulkUpdateSettingsRequest) error {
	// Build a map accumulator of updates per keyword_id
	upd := map[uint]*entities.PreferenceBlacklist{}
	ensure := func(id uint) *entities.PreferenceBlacklist {
		if upd[id] == nil {
			upd[id] = &entities.PreferenceBlacklist{UserID: userID, KeywordID: id}
		}
		return upd[id]
	}
	// 1) Start from explicit settings payload to preserve current behavior
	for _, u := range req.Settings {
		cur := ensure(u.KeywordID)
		cur.Preference = u.PreferenceValue
		cur.Blacklist = u.BlacklistValue
	}
	// 2) Expand normalized English selections into keyword_id updates
	// Helper to set group values
	setGroup := func(groups map[string]map[uint]struct{}, selected []string, setPref bool, setBlack bool) {
		sel := map[string]struct{}{}
		for _, s := range selected {
			sel[s] = struct{}{}
		}
		for en, ids := range groups {
			valPref := 0.0
			valBlack := 0.0
			if _, ok := sel[en]; ok {
				if setPref {
					valPref = 1.0
				}
				if setBlack {
					valBlack = 1.0
				}
			}
			for id := range ids {
				cur := ensure(id)
				// Only override the aspects we’re setting; preserve the other if already set explicitly
				if setPref {
					cur.Preference = valPref
				}
				if setBlack {
					cur.Blacklist = valBlack
				}
			}
		}
	}
	// Preferences
	if len(req.FlavorENPreferred) > 0 {
		setGroup(s.flavorENToIDs, req.FlavorENPreferred, true, false)
	}
	if len(req.CostENPreferred) > 0 {
		setGroup(s.costENToIDs, req.CostENPreferred, true, false)
	}
	// Blacklists
	if len(req.FlavorENBlacklisted) > 0 {
		setGroup(s.flavorENToIDs, req.FlavorENBlacklisted, false, true)
	}
	if len(req.CostENBlacklisted) > 0 {
		setGroup(s.costENToIDs, req.CostENBlacklisted, false, true)
	}

	// 3) Convert to slice and persist
	out := make([]entities.PreferenceBlacklist, 0, len(upd))
	for _, v := range upd {
		out = append(out, *v)
	}
	if len(out) == 0 {
		return nil
	}
	return s.recommendRepo.BulkUpdateUserSettings(userID, out)
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
	var dishName string
	if dish, derr := s.foodRepo.GetDishByID(req.DishID); derr == nil {
		dishName = dish.DishName
		if res, rerr := s.foodRepo.GetRestaurantByID(dish.ResID); rerr == nil {
			restaurantName = res.ResName
		}
	}
	if restaurantName == "" {
		restaurantName = ""
	}

	// Construct command: python -m llm_processing.single_review ...
	// Resolve Python executable robustly
	pyExec := os.Getenv("PYTHON_EXEC")
	if pyExec == "" {
		pyExec = os.Getenv("PYTHON_BIN")
	}
	if pyExec == "" {
		pyExec = "python"
	}
	if resolved, err := exec.LookPath(pyExec); err == nil {
		pyExec = resolved
	}
	// Prefer project-local virtualenv if available: <repo>/.venv/bin|Scripts/python
	if wd, _ := os.Getwd(); wd != "" {
		projectRoot := filepath.Dir(wd)
		var venvCandidate string
		if runtime.GOOS == "windows" {
			venvCandidate = filepath.Join(projectRoot, ".venv", "Scripts", "python.exe")
		} else {
			venvCandidate = filepath.Join(projectRoot, ".venv", "bin", "python")
		}
		if st, err := os.Stat(venvCandidate); err == nil && !st.IsDir() {
			pyExec = venvCandidate
		}
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
	// Make Python output unbuffered for realtime logs
	env = append(env, "PYTHONUNBUFFERED=1")
	// Expose the resolved Python exec path for diagnostics
	env = append(env, fmt.Sprintf("%s=%s", "PYTHON_EXEC_USED", pyExec))
	// Tag this ingestion as user-sourced for downstream auditing
	env = append(env, "SOURCE_TYPE=user")
	// Provide hint values so Python can write a fallback entry if extraction yields no dishes
	env = append(env, fmt.Sprintf("%s=%d", "HINT_DISH_ID", req.DishID))
	env = append(env, fmt.Sprintf("%s=%d", "HINT_RES_ID", req.ResID))
	if dishName != "" {
		env = append(env, fmt.Sprintf("%s=%s", "HINT_DISH_NAME", dishName))
	}
	if restaurantName != "" {
		env = append(env, fmt.Sprintf("%s=%s", "HINT_RES_NAME", restaurantName))
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

	// Capture stdout/stderr to a per-review log file for debugging
	logDir := filepath.Join("logs")
	_ = os.MkdirAll(logDir, 0o755)
	logFilePath := filepath.Join(logDir, fmt.Sprintf("llm_job_user_%d.log", reviewID))
	lf, lfErr := os.Create(logFilePath)
	if lfErr == nil {
		// Write a small header into the log for easier troubleshooting
		_, _ = lf.WriteString("==== DishDive LLM job ====" + "\n")
		_, _ = lf.WriteString("Working Dir: " + cmd.Dir + "\n")
		_, _ = lf.WriteString("Python Exec: " + pyExec + "\n")
		if pp := os.Getenv("PYTHONPATH"); pp != "" {
			_, _ = lf.WriteString("PYTHONPATH: " + pp + "\n")
		}
		_, _ = lf.WriteString("=========================\n")
		cmd.Stdout = lf
		cmd.Stderr = lf
		fmt.Printf("[llm] logging subprocess output to %s\n", logFilePath)
	} else {
		fmt.Printf("[llm] could not create log file: %v\n", lfErr)
	}

	// Start without waiting; log if it fails to start
	if err := cmd.Start(); err != nil {
		fmt.Printf("[llm] failed to start single_review processor: %v\n", err)
		if lfErr == nil {
			_ = lf.Close()
		}
	} else {
		go func() {
			if werr := cmd.Wait(); werr != nil {
				fmt.Printf("[llm] processor exited with error: %v\n", werr)
			} else {
				fmt.Printf("[llm] processor completed for review_id=%d\n", reviewID)
			}
			if lfErr == nil {
				_ = lf.Close()
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
		dish      entities.Dish
		score     float64
		isFav     bool
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
		if sentimentBlacklist > 0 && sentimentPercentage < (sentimentBlacklist*100) {
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
		if sentimentPreference > 0 && sentimentPercentage > (sentimentPreference*100) {
			score += 20
		}

		// Favorites boost (x3)
		if isFav {
			score *= 3.0
		}

		// Debug log: Final score for the dish
		// fmt.Printf("DishID: %d, Final Score: %.2f\n", dish.DishID, score)

		scoredDishes = append(scoredDishes, scoredDish{
			dish:      dish,
			score:     score,
			isFav:     isFav,
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
			imageURL, err := s.foodRepo.GetCuisineImageByCuisineAndTag(*sd.dish.Cuisine, nil)
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

func (s *recommendService) HasNormalizedReview(sourceID uint) (bool, error) {
	return s.recommendRepo.HasNormalizedReview(sourceID)
}

// Helper function to get cuisine image link
func getCuisineImageLink(foodRepo repository.FoodRepository, cuisine *string) *string {
	if cuisine == nil {
		return nil
	}

	imageURL, err := foodRepo.GetCuisineImageByCuisineAndTag(*cuisine, nil)
	if err != nil || imageURL == "" {
		return nil
	}

	return &imageURL
}
