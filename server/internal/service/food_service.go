package service

import (
	"fmt"
	"math"
	"strings"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/entities"
	"github.com/bestchayapol/DishDive/internal/repository"
)

type foodService struct {
	foodRepo repository.FoodRepository
}

// Update constructor to match new interface
func NewFoodService(foodRepo repository.FoodRepository) *foodService {
	return &foodService{foodRepo: foodRepo}
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
	var resp []dtos.SearchRestaurantsByDishResponse
	for _, r := range restaurants {
		// Get cuisine image
		var imageLink *string
		if r.ResCuisine != nil {
			imageURL, err := s.foodRepo.GetCuisineImageByCuisine(*r.ResCuisine)
			if err == nil && imageURL != "" {
				imageLink = &imageURL
			}
		}

		resp = append(resp, dtos.SearchRestaurantsByDishResponse{
			ResID:     r.ResID,
			ResName:   r.ResName,
			ImageLink: imageLink,
			Cuisine:   r.ResCuisine,
			// Location and Distance can be filled if you have that logic
		})
	}
	return resp, nil
}

func (s *foodService) GetRestaurantList() ([]dtos.RestaurantListItemResponse, error) {
	restaurants, err := s.foodRepo.GetAllRestaurants()
	if err != nil {
		return nil, err
	}
	var resp []dtos.RestaurantListItemResponse
	for _, r := range restaurants {
		// Get cuisine image
		var imageLink *string
		if r.ResCuisine != nil {
			imageURL, err := s.foodRepo.GetCuisineImageByCuisine(*r.ResCuisine)
			if err == nil && imageURL != "" {
				imageLink = &imageURL
			}
		}

		resp = append(resp, dtos.RestaurantListItemResponse{
			ResID:     r.ResID,
			ResName:   r.ResName,
			ImageLink: imageLink,
			Cuisine:   r.ResCuisine,
		})
	}
	return resp, nil
}

func (s *foodService) GetRestaurantMenu(resID uint, userID uint) ([]dtos.RestaurantMenuItemResponse, error) {
	dishes, err := s.foodRepo.GetDishesByRestaurant(resID)
	if err != nil {
		return nil, err
	}

	var resp []dtos.RestaurantMenuItemResponse
	for _, dish := range dishes {
		// Get cuisine image
		var imageLink *string
		if dish.Cuisine != nil {
			imageURL, err := s.foodRepo.GetCuisineImageByCuisine(*dish.Cuisine)
			if err == nil && imageURL != "" {
				imageLink = &imageURL
			}
		}

		// Get prominent flavor
		prominentFlavor, err := s.foodRepo.GetProminentFlavorByDish(dish.DishID)
		if err != nil {
			prominentFlavor = nil // Set to nil if error
		}

		// Check if favorite
		isFav, _ := s.foodRepo.IsFavoriteDish(userID, dish.DishID)

		resp = append(resp, dtos.RestaurantMenuItemResponse{
			DishID:          dish.DishID,
			DishName:        dish.DishName,
			ImageLink:       imageLink,
			SentimentScore:  dish.TotalScore,
			Cuisine:         dish.Cuisine,
			ProminentFlavor: prominentFlavor,
			IsFavorite:      isFav,
			RecommendScore:  0.0, // TODO: Calculate if needed for restaurant menu
		})
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
		imageURL, err := s.foodRepo.GetCuisineImageByCuisine(*dish.Cuisine)
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
		SentimentScore:  dish.TotalScore,
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
			imageURL, err := s.foodRepo.GetCuisineImageByCuisine(*d.Cuisine)
			if err == nil && imageURL != "" {
				imageLink = &imageURL
			}
		}

		resp = append(resp, dtos.FavoriteDishResponse{
			DishID:          d.DishID,
			DishName:        d.DishName,
			ImageLink:       imageLink,
			SentimentScore:  d.TotalScore,
			Cuisine:         d.Cuisine,
			ProminentFlavor: nil, // Fill as needed
		})
	}
	return resp, nil
}

func (s *foodService) AddFavorite(userID uint, dishID uint) error {
	return s.foodRepo.AddFavoriteDish(userID, dishID)
}

func (s *foodService) RemoveFavorite(userID uint, dishID uint) error {
	return s.foodRepo.RemoveFavoriteDish(userID, dishID)
}
