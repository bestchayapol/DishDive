package service

import (
	"github.com/bestchayapol/DishDive/internal/dtos"
)

type FoodService interface {
	SearchRestaurantsByDish(req dtos.SearchRestaurantsByDishRequest) ([]dtos.SearchRestaurantsByDishResponse, error)
	GetRestaurantList(userLat *float64, userLng *float64, radius *float64, userID *uint) ([]dtos.RestaurantListItemResponse, error)
	GetDishDetail(dishID uint, userID uint) (dtos.DishDetailResponse, error)
	GetFavoriteDishes(userID uint) ([]dtos.FavoriteDishResponse, error)
	AddFavorite(userID uint, dishID uint) error
	RemoveFavorite(userID uint, dishID uint) error
	GetLocationsByRestaurant(resID uint, userLat, userLng float64) ([]dtos.RestaurantLocationResponse, error)
	AddOrUpdateLocation(location dtos.RestaurantLocationResponse) error
}
