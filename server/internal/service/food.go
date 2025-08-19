package service

import (
	"github.com/bestchayapol/DishDive/internal/dtos"
)

type FoodService interface {
	SearchRestaurantsByDish(req dtos.SearchRestaurantsByDishRequest) ([]dtos.SearchRestaurantsByDishResponse, error)
	GetRestaurantList() ([]dtos.RestaurantListItemResponse, error)
	GetRestaurantMenu(resID uint) ([]dtos.RestaurantMenuItemResponse, error)
	GetDishDetail(dishID uint, userID uint) (dtos.DishDetailResponse, error)
	GetFavoriteDishes(userID uint) ([]dtos.FavoriteDishResponse, error)
	RemoveFavorite(req dtos.RemoveFavoriteRequest) (dtos.RemoveFavoriteResponse, error)

	// RestaurantLocation-related
	GetLocationsByRestaurant(resID uint, userLat, userLng float64) ([]dtos.RestaurantLocationResponse, error)
	AddOrUpdateLocation(location dtos.RestaurantLocationResponse) error
}
