package repository

import (
	"github.com/bestchayapol/DishDive/internal/entities"
)

type FoodRepository interface {
	// Restaurant-related
	GetAllRestaurants() ([]entities.Restaurant, error)
	GetRestaurantByID(resID uint) (*entities.Restaurant, error)
	SearchRestaurantsByDish(dishName string, latitude, longitude, radius float64) ([]entities.Restaurant, error)

	// Dish-related
	GetAllDishes() ([]entities.Dish, error)
	GetDishByID(dishID uint) (*entities.Dish, error)
	GetDishesByRestaurant(resID uint) ([]entities.Dish, error)

	// Favorite-related
	GetFavoriteDishesByUser(userID uint) ([]entities.Dish, error)
	AddFavoriteDish(userID uint, dishID uint) error
	RemoveFavoriteDish(userID uint, dishID uint) error
	IsFavoriteDish(userID uint, dishID uint) (bool, error)
}
