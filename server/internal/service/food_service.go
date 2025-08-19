package service

import (
    "github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/entities"
    "github.com/bestchayapol/DishDive/internal/repository"
)

type foodService struct {
    foodRepo repository.FoodRepository
}

// RestaurantLocation methods
func (s *foodService) GetLocationsByRestaurant(resID uint) ([]dtos.RestaurantLocationResponse, error) {
    locations, err := s.foodRepo.GetLocationsByRestaurant(resID)
    if err != nil {
        return nil, err
    }
    var resp []dtos.RestaurantLocationResponse
    for _, loc := range locations {
        resp = append(resp, dtos.RestaurantLocationResponse{
            RLID:         loc.RLID,
            LocationName: loc.LocationName,
            Address:      loc.Address,
            Latitude:     loc.Latitude,
            Longitude:    loc.Longitude,
            // Distance: fill if needed
        })
    }
    return resp, nil
}

func (s *foodService) AddOrUpdateLocation(location dtos.RestaurantLocationResponse) error {
    loc := &entities.RestaurantLocation{
        RLID:         location.RLID,
        ResID:        0, // Fill as needed
        LocationName: location.LocationName,
        Address:      location.Address,
        Latitude:     location.Latitude,
        Longitude:    location.Longitude,
    }
    return s.foodRepo.AddOrUpdateLocation(loc)
}

func NewFoodService(foodRepo repository.FoodRepository) FoodService {
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

func (s *foodService) GetRestaurantMenu(resID uint) ([]dtos.RestaurantMenuItemResponse, error) {
    dishes, err := s.foodRepo.GetDishesByRestaurant(resID)
    if err != nil {
        return nil, err
    }
    var resp []dtos.RestaurantMenuItemResponse
    for _, d := range dishes {
        resp = append(resp, dtos.RestaurantMenuItemResponse{
            DishID:          d.DishID,
            DishName:        d.DishName,
            ImageLink:       nil, // Fill as needed
            SentimentScore:  d.TotalScore,
            Cuisine:         d.Cuisine,
            ProminentFlavor: nil, // Fill as needed
            IsFavorite:      false, // Fill as needed
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
        ProminentFlavor: nil, // Fill as needed
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

func (s *foodService) RemoveFavorite(req dtos.RemoveFavoriteRequest) (dtos.RemoveFavoriteResponse, error) {
    err := s.foodRepo.RemoveFavoriteDish(0, req.DishID) // Fill userID as needed
    return dtos.RemoveFavoriteResponse{Success: err == nil}, err
}