package repository

import (
	"github.com/bestchayapol/DishDive/internal/entities"
)

// Custom struct for dish keywords with frequency data
type DishKeywordWithFrequency struct {
	Keyword   string `json:"keyword"`
	Category  string `json:"category"`
	Frequency int    `json:"frequency"`
}

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

	// RestaurantLocation-related
	GetLocationsByRestaurant(resID uint) ([]entities.RestaurantLocation, error)
	AddOrUpdateLocation(location *entities.RestaurantLocation) error

	// Dish-keyword mapping
	GetKeywordsByDish(dishID uint) ([]entities.Keyword, error)
	GetProminentFlavorByDish(dishID uint) (*string, error)
	GetTopKeywordsByDishWithFrequency(dishID uint) ([]DishKeywordWithFrequency, error)
	GetReviewCountsByDish(dishID uint) (positiveReviews int, totalReviews int, err error)

	// Image-related
	GetCuisineImageByCuisine(cuisine string) (string, error)
}
