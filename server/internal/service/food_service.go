package service

import (
	"fmt"
	"math"
	"sort"
	"strings"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/entities"
	"github.com/bestchayapol/DishDive/internal/repository"
)

type foodService struct {
	foodRepo      repository.FoodRepository
	recommendRepo repository.RecommendRepository
}

// Preference-aware soft boost tuning knobs (km)
const (
	flavorBoostPerMatchKm  = 0.20
	costBoostPerMatchKm    = 0.10
	maxPreferenceBoostKm   = 0.60
	maxDishesPerRestaurant = 5
)

// Update constructor to match new interface
func NewFoodService(foodRepo repository.FoodRepository, recommendRepo repository.RecommendRepository) *foodService {
	return &foodService{foodRepo: foodRepo, recommendRepo: recommendRepo}
}

// RestaurantLocation methods
// GetLocationsByRestaurant now takes userLat, userLng for distance calculation
func (s *foodService) GetLocationsByRestaurant(resID uint, userLat, userLng float64) ([]dtos.RestaurantLocationResponse, error) {
	locations, err := s.foodRepo.GetLocationsByRestaurant(resID)
	if err != nil {
		return nil, err
	}
	var resp []dtos.RestaurantLocationResponse
	for _, loc := range locations {
		dist := calculateDistance(userLat, userLng, loc.Latitude, loc.Longitude)
		resp = append(resp, dtos.RestaurantLocationResponse{
			RLID:         loc.RLID,
			LocationName: loc.LocationName,
			Address:      loc.Address,
			Latitude:     loc.Latitude,
			Longitude:    loc.Longitude,
			Distance:     dist,
		})
	}
	return resp, nil
}

// Haversine formula for distance in kilometers
func calculateDistance(lat1, lng1, lat2, lng2 float64) float64 {
	const R = 6371 // Earth radius in km
	dLat := (lat2 - lat1) * 0.0174533
	dLng := (lng2 - lng1) * 0.0174533
	a := 0.5 - (math.Cos(dLat) / 2) + math.Cos(lat1*0.0174533)*math.Cos(lat2*0.0174533)*(1-math.Cos(dLng))/2
	return R * 2 * math.Asin(math.Sqrt(a))
}

func (s *foodService) AddOrUpdateLocation(location dtos.RestaurantLocationResponse) error {
	loc := &entities.RestaurantLocation{
		RLID:         location.RLID,
		ResID:        location.ResID,
		LocationName: location.LocationName,
		Address:      location.Address,
		Latitude:     location.Latitude,
		Longitude:    location.Longitude,
	}
	return s.foodRepo.AddOrUpdateLocation(loc)
}

func (s *foodService) SearchRestaurantsByDish(req dtos.SearchRestaurantsByDishRequest) ([]dtos.SearchRestaurantsByDishResponse, error) {
	restaurants, err := s.foodRepo.SearchRestaurantsByDish(req.DishName, req.Latitude, req.Longitude, req.Radius)
	if err != nil {
		return nil, err
	}
	type item struct {
		dto      dtos.SearchRestaurantsByDishResponse
		distance float64
	}
	var items []item
	for _, r := range restaurants {
		// Get cuisine image
		var imageLink *string
		if r.ResCuisine != nil {
			imageURL, err := s.foodRepo.GetCuisineImageByCuisineAndTag(*r.ResCuisine, r.ImageTag)
			if err == nil && imageURL != "" {
				imageLink = &imageURL
			}
		}
		// Pick nearest valid location and compute distance if user coords provided
		var locDTO dtos.RestaurantLocationResponse
		nearestDist := 0.0
		if locs, lerr := s.foodRepo.GetLocationsByRestaurant(r.ResID); lerr == nil && len(locs) > 0 {
			// Default to first
			l := locs[0]
			locDTO = dtos.RestaurantLocationResponse{
				RLID:         l.RLID,
				ResID:        l.ResID,
				LocationName: l.LocationName,
				Address:      l.Address,
				Latitude:     l.Latitude,
				Longitude:    l.Longitude,
			}
			// If user lat/lng provided, compute nearest
			if req.Latitude != 0 || req.Longitude != 0 { // treat as provided if non-zero
				best := calculateDistance(req.Latitude, req.Longitude, l.Latitude, l.Longitude)
				bestIdx := 0
				for i := 1; i < len(locs); i++ {
					d := calculateDistance(req.Latitude, req.Longitude, locs[i].Latitude, locs[i].Longitude)
					if d < best {
						best = d
						bestIdx = i
					}
				}
				ll := locs[bestIdx]
				locDTO = dtos.RestaurantLocationResponse{
					RLID:         ll.RLID,
					ResID:        ll.ResID,
					LocationName: ll.LocationName,
					Address:      ll.Address,
					Latitude:     ll.Latitude,
					Longitude:    ll.Longitude,
					Distance:     best,
				}
				nearestDist = best
			}
		}

		items = append(items, item{dto: dtos.SearchRestaurantsByDishResponse{
			ResID:     r.ResID,
			ResName:   r.ResName,
			ImageLink: imageLink,
			Cuisine:   r.ResCuisine,
			Location:  locDTO,
			Distance:  locDTO.Distance,
		}, distance: nearestDist})
	}
	// Optional radius filter
	if req.Radius > 0 && (req.Latitude != 0 || req.Longitude != 0) {
		filtered := make([]item, 0, len(items))
		for _, it := range items {
			if it.distance >= 0 && it.distance <= req.Radius {
				filtered = append(filtered, it)
			}
		}
		if len(filtered) > 0 {
			items = filtered
		}
	}
	// Sort by distance if provided (preference-aware ranking can be added here when user_id available)
	if req.Latitude != 0 || req.Longitude != 0 {
		sort.Slice(items, func(i, j int) bool { return items[i].distance < items[j].distance })
	}
	// Build response
	resp := make([]dtos.SearchRestaurantsByDishResponse, 0, len(items))
	for _, it := range items {
		resp = append(resp, it.dto)
	}
	return resp, nil
}

func (s *foodService) GetRestaurantList(userLat *float64, userLng *float64, radius *float64, userID *uint) ([]dtos.RestaurantListItemResponse, error) {
	restaurants, err := s.foodRepo.GetAllRestaurants()
	if err != nil {
		return nil, err
	}
	// Build blacklist cuisine set if userID provided
	blacklistedCuisine := map[string]struct{}{}
	if userID != nil {
		if settings, err := s.recommendRepo.GetUserSettings(*userID); err == nil {
			for _, st := range settings {
				if st.Blacklist > 0 {
					if kw, kerr := s.recommendRepo.GetKeywordByID(st.KeywordID); kerr == nil {
						if strings.ToLower(kw.Category) == "cuisine" {
							blacklistedCuisine[kw.Keyword] = struct{}{}
						}
					}
				}
			}
		}
	}

	// Build preferred keyword-id sets for flavor/cost (used for soft-boost)
	preferredFlavorIDs := map[uint]struct{}{}
	preferredCostIDs := map[uint]struct{}{}
	hasPreferences := false
	if userID != nil {
		// Fetch all flavor/cost keywords to avoid per-setting lookups
		if kws, err := s.recommendRepo.GetKeywordsByCategory([]string{"flavor", "cost"}); err == nil {
			flavorUniverse := map[uint]struct{}{}
			costUniverse := map[uint]struct{}{}
			for _, kw := range kws {
				switch strings.ToLower(kw.Category) {
				case "flavor":
					flavorUniverse[kw.KeywordID] = struct{}{}
				case "cost":
					costUniverse[kw.KeywordID] = struct{}{}
				}
			}
			if settings, err := s.recommendRepo.GetUserSettings(*userID); err == nil {
				for _, st := range settings {
					if st.Preference > 0 {
						if _, ok := flavorUniverse[st.KeywordID]; ok {
							preferredFlavorIDs[st.KeywordID] = struct{}{}
							hasPreferences = true
						} else if _, ok := costUniverse[st.KeywordID]; ok {
							preferredCostIDs[st.KeywordID] = struct{}{}
							hasPreferences = true
						}
					}
				}
			}
		}
	}
	type item struct {
		dto         dtos.RestaurantListItemResponse
		distance    float64 // nearest branch distance
		effDistance float64 // effective distance after preference boost
	}
	var items []item
	for _, r := range restaurants {
		// Apply cuisine blacklist filter if available
		if userID != nil && r.ResCuisine != nil {
			if _, banned := blacklistedCuisine[*r.ResCuisine]; banned {
				continue
			}
		}
		// Get cuisine image
		var imageLink *string
		if r.ResCuisine != nil {
			imageURL, err := s.foodRepo.GetCuisineImageByCuisineAndTag(*r.ResCuisine, r.ImageTag)
			if err == nil && imageURL != "" {
				imageLink = &imageURL
			}
		}

		// Fetch valid locations for the restaurant (already filtered in repo)
		var locsDTO []dtos.RestaurantLocationResponse
		nearest := 0.0
		if locs, lerr := s.foodRepo.GetLocationsByRestaurant(r.ResID); lerr == nil {
			for _, l := range locs {
				d := 0.0
				if userLat != nil && userLng != nil {
					d = calculateDistance(*userLat, *userLng, l.Latitude, l.Longitude)
					if nearest == 0 || d < nearest {
						nearest = d
					}
				}
				locsDTO = append(locsDTO, dtos.RestaurantLocationResponse{
					RLID:         l.RLID,
					ResID:        l.ResID,
					LocationName: l.LocationName,
					Address:      l.Address,
					Latitude:     l.Latitude,
					Longitude:    l.Longitude,
					Distance:     d,
				})
			}
		}
		items = append(items, item{dto: dtos.RestaurantListItemResponse{
			ResID:     r.ResID,
			ResName:   r.ResName,
			ImageLink: imageLink,
			Cuisine:   r.ResCuisine,
			Locations: locsDTO,
		}, distance: nearest})
	}
	// Optional radius filter
	if radius != nil && userLat != nil && userLng != nil && *radius > 0 {
		filtered := make([]item, 0, len(items))
		for _, it := range items {
			if it.distance >= 0 && it.distance <= *radius {
				filtered = append(filtered, it)
			}
		}
		if len(filtered) > 0 {
			items = filtered
		}
	}
	// Compute preference-aware effective distance (soft boost) and sort by it if applicable
	if userLat != nil && userLng != nil {
		for idx := range items {
			it := &items[idx]
			eff := it.distance
			// Apply soft boost only when we have a distance, a user, and preferences
			if userID != nil && hasPreferences && it.distance > 0 {
				// Sample a few dishes from this restaurant and count unique preferred matches
				flavorMatches := map[uint]struct{}{}
				costMatches := map[uint]struct{}{}
				if dishes, err := s.foodRepo.GetDishesByRestaurant(it.dto.ResID); err == nil && len(dishes) > 0 {
					limit := len(dishes)
					if limit > maxDishesPerRestaurant {
						limit = maxDishesPerRestaurant
					}
					for di := 0; di < limit; di++ {
						if kws, err := s.foodRepo.GetKeywordsByDish(dishes[di].DishID); err == nil {
							for _, kw := range kws {
								if _, ok := preferredFlavorIDs[kw.KeywordID]; ok {
									flavorMatches[kw.KeywordID] = struct{}{}
								} else if _, ok := preferredCostIDs[kw.KeywordID]; ok {
									costMatches[kw.KeywordID] = struct{}{}
								}
							}
						}
					}
				}
				// Compute total km boost with cap
				boostKm := float64(len(flavorMatches))*flavorBoostPerMatchKm + float64(len(costMatches))*costBoostPerMatchKm
				if boostKm > maxPreferenceBoostKm {
					boostKm = maxPreferenceBoostKm
				}
				if boostKm > 0 {
					eff = it.distance - boostKm
					if eff < 0 {
						eff = 0
					}
				}
			}
			it.effDistance = eff
		}
		sort.Slice(items, func(i, j int) bool {
			// If both have effective distances computed (non-zero distance), compare those
			return items[i].effDistance < items[j].effDistance
		})
	}
	resp := make([]dtos.RestaurantListItemResponse, 0, len(items))
	for _, it := range items {
		resp = append(resp, it.dto)
	}
	return resp, nil
}

func (s *foodService) GetDishDetail(dishID uint, userID uint) (dtos.DishDetailResponse, error) {
	dish, err := s.foodRepo.GetDishByID(dishID)
	if err != nil {
		return dtos.DishDetailResponse{}, err
	}

	// Get cuisine image
	var imageLink *string
	if dish.Cuisine != nil {
		imageURL, err := s.foodRepo.GetCuisineImageByCuisineAndTag(*dish.Cuisine, nil)
		if err == nil && imageURL != "" {
			imageLink = &imageURL
		}
	}

	// Get prominent flavor
	prominentFlavor, err := s.foodRepo.GetProminentFlavorByDish(dishID)
	if err != nil {
		prominentFlavor = nil
	}

	// Get review counts
	positiveReviews, totalReviews, err := s.foodRepo.GetReviewCountsByDish(dishID)
	if err != nil {
		positiveReviews, totalReviews = 0, 0
	}

	// Calculate sentiment score: positive score / total score
	var sentimentScore float64 = 0
	if totalReviews > 0 {
		sentimentScore = float64(positiveReviews) / float64(totalReviews) * 100 // Convert to percentage
	}

	// Get top keywords by category
	keywords, err := s.foodRepo.GetTopKeywordsByDishWithFrequency(dishID)
	topKeywords := make(map[string][]string)
	if err == nil {
		flavorKeywords := []string{}
		costKeywords := []string{}
		generalKeywords := []string{}

		for _, kw := range keywords {
			keywordWithCount := kw.Keyword + " (" + fmt.Sprintf("%d", kw.Frequency) + ")"
			switch strings.ToLower(kw.Category) {
			case "flavor", "taste":
				flavorKeywords = append(flavorKeywords, keywordWithCount)
			case "cost", "price":
				costKeywords = append(costKeywords, keywordWithCount)
			default:
				generalKeywords = append(generalKeywords, keywordWithCount)
			}
		}

		topKeywords["flavor"] = flavorKeywords
		topKeywords["cost"] = costKeywords
		topKeywords["general"] = generalKeywords
	}

	// Check if favorite
	isFav, _ := s.foodRepo.IsFavoriteDish(userID, dishID)

	return dtos.DishDetailResponse{
		DishID:          dish.DishID,
		DishName:        dish.DishName,
		ImageLink:       imageLink,
		SentimentScore:  sentimentScore,
		PositiveReviews: positiveReviews,
		TotalReviews:    totalReviews,
		Cuisine:         dish.Cuisine,
		ProminentFlavor: prominentFlavor,
		TopKeywords:     topKeywords,
		IsFavorite:      isFav,
	}, nil
}

func (s *foodService) GetFavoriteDishes(userID uint) ([]dtos.FavoriteDishResponse, error) {
	dishes, err := s.foodRepo.GetFavoriteDishesByUser(userID)
	if err != nil {
		return nil, err
	}
	var resp []dtos.FavoriteDishResponse
	for _, d := range dishes {
		// Get cuisine image
		var imageLink *string
		if d.Cuisine != nil {
			imageURL, err := s.foodRepo.GetCuisineImageByCuisineAndTag(*d.Cuisine, nil)
			if err == nil && imageURL != "" {
				imageLink = &imageURL
			}
		}

		// Get prominent flavor
		prominentFlavor, err := s.foodRepo.GetProminentFlavorByDish(d.DishID)
		if err != nil {
			prominentFlavor = nil
		}

		// Get review counts
		positiveReviews, totalReviews, err := s.foodRepo.GetReviewCountsByDish(d.DishID)
		if err != nil {
			positiveReviews, totalReviews = 0, 0
		}

		// Calculate sentiment score: positive score / total score
		var sentimentScore float64 = 0
		if totalReviews > 0 {
			sentimentScore = float64(positiveReviews) / float64(totalReviews) * 100 // Convert to percentage
		}

		resp = append(resp, dtos.FavoriteDishResponse{
			DishID:          d.DishID,
			DishName:        d.DishName,
			ImageLink:       imageLink,
			SentimentScore:  sentimentScore,
			PositiveReviews: positiveReviews,
			TotalReviews:    totalReviews,
			Cuisine:         d.Cuisine,
			ProminentFlavor: prominentFlavor,
		})
	}

	// Sort favorites by sentiment score in descending order as well
	sort.Slice(resp, func(i, j int) bool {
		return resp[i].SentimentScore > resp[j].SentimentScore
	})

	return resp, nil
}

func (s *foodService) AddFavorite(userID uint, dishID uint) error {
	return s.foodRepo.AddFavoriteDish(userID, dishID)
}

func (s *foodService) RemoveFavorite(userID uint, dishID uint) error {
	return s.foodRepo.RemoveFavoriteDish(userID, dishID)
}
