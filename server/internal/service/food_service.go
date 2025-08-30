package service

import (
	"math"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/entities"
	"github.com/bestchayapol/DishDive/internal/repository"
)

type foodService struct {
	foodRepo repository.FoodRepository
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

// Update constructor to match new interface
func NewFoodService(foodRepo repository.FoodRepository) *foodService {
	return &foodService{foodRepo: foodRepo}
}

func (s *foodService) SearchRestaurantsByDish(req dtos.SearchRestaurantsByDishRequest) ([]dtos.SearchRestaurantsByDishResponse, error) {
	restaurants, err := s.foodRepo.SearchRestaurantsByDish(req.DishName, req.Latitude, req.Longitude, req.Radius)
	if err != nil {
		return nil, err
	}
	var resp []dtos.SearchRestaurantsByDishResponse
	for _, r := range restaurants {
		resp = append(resp, dtos.SearchRestaurantsByDishResponse{
			ResID:     r.ResID,
			ResName:   r.ResName,
			ImageLink: nil, // Fill as needed
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
		resp = append(resp, dtos.RestaurantListItemResponse{
			ResID:     r.ResID,
			ResName:   r.ResName,
			ImageLink: nil, // Fill as needed
			Cuisine:   r.ResCuisine,
			// Locations can be filled if you have that logic
		})
	}
	return resp, nil
}

func (s *foodService) GetRestaurantMenuWithUserData(resID uint, userID uint) ([]dtos.RestaurantMenuItemResponse, error) {
    dishes, err := s.foodRepo.GetDishesByRestaurant(resID)
    if err != nil {
        return nil, err
    }
    var resp []dtos.RestaurantMenuItemResponse
    for _, d := range dishes {
        isFav, _ := s.foodRepo.IsFavoriteDish(userID, d.DishID)
        // Calculate percentage score
        var percentage float64
        if d.PositiveScore+d.NegativeScore > 0 {
            percentage = float64(d.PositiveScore) / float64(d.PositiveScore+d.NegativeScore) * 100
        }
        
        resp = append(resp, dtos.RestaurantMenuItemResponse{
            DishID:          d.DishID,
            DishName:        d.DishName,
            ImageLink:       nil, // Fill as needed
            SentimentScore:  percentage,
            Cuisine:         d.Cuisine,
            ProminentFlavor: nil, // Fill as needed
            IsFavorite:      isFav,
        })
    }
    return resp, nil
}

func (s *foodService) GetDishDetail(dishID uint, userID uint) (dtos.DishDetailResponse, error) {
	dish, err := s.foodRepo.GetDishByID(dishID)
	if err != nil {
		return dtos.DishDetailResponse{}, err
	}
	isFav, _ := s.foodRepo.IsFavoriteDish(userID, dishID)
	return dtos.DishDetailResponse{
		DishID:          dish.DishID,
		DishName:        dish.DishName,
		ImageLink:       nil, // Fill as needed
		SentimentScore:  dish.TotalScore,
		Cuisine:         dish.Cuisine,
		ProminentFlavor: nil,                   // Fill as needed
		TopKeywords:     map[string][]string{}, // Fill as needed
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
		resp = append(resp, dtos.FavoriteDishResponse{
			DishID:          d.DishID,
			DishName:        d.DishName,
			ImageLink:       nil, // Fill as needed
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