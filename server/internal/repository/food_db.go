package repository

import (
	"github.com/bestchayapol/DishDive/internal/entities"
	"gorm.io/gorm"
)

type foodRepositoryDB struct {
	db *gorm.DB
}

func NewFoodRepositoryDB(db *gorm.DB) FoodRepository {
	return &foodRepositoryDB{db: db}
}

// RestaurantLocation methods
func (r *foodRepositoryDB) GetLocationsByRestaurant(resID uint) ([]entities.RestaurantLocation, error) {
	var locations []entities.RestaurantLocation
	result := r.db.Where("res_id = ?", resID).Find(&locations)
	return locations, result.Error
}

func (r *foodRepositoryDB) AddOrUpdateLocation(location *entities.RestaurantLocation) error {
	// If RLID is zero, create new; else update existing
	if location.RLID == 0 {
		return r.db.Create(location).Error
	}
	return r.db.Save(location).Error
}


// Restaurant methods
func (r *foodRepositoryDB) GetAllRestaurants() ([]entities.Restaurant, error) {
	var restaurants []entities.Restaurant
	result := r.db.Find(&restaurants)
	return restaurants, result.Error
}

func (r *foodRepositoryDB) GetRestaurantByID(resID uint) (*entities.Restaurant, error) {
	var restaurant entities.Restaurant
	result := r.db.Where("res_id = ?", resID).First(&restaurant)
	if result.Error != nil {
		return nil, result.Error
	}
	return &restaurant, nil
}

func (r *foodRepositoryDB) SearchRestaurantsByDish(dishName string, latitude, longitude, radius float64) ([]entities.Restaurant, error) {
	var restaurants []entities.Restaurant
	// Example: join dishes and filter by dish name. You can add location filtering later.
	result := r.db.Joins("JOIN dishes ON dishes.res_id = restaurants.res_id").
		Where("dishes.dish_name LIKE ?", "%"+dishName+"%").
		Find(&restaurants)
	return restaurants, result.Error
}

// Dish methods
func (r *foodRepositoryDB) GetAllDishes() ([]entities.Dish, error) {
	var dishes []entities.Dish
	result := r.db.Find(&dishes)
	return dishes, result.Error
}

func (r *foodRepositoryDB) GetDishByID(dishID uint) (*entities.Dish, error) {
	var dish entities.Dish
	result := r.db.Where("dish_id = ?", dishID).First(&dish)
	if result.Error != nil {
		return nil, result.Error
	}
	return &dish, nil
}

func (r *foodRepositoryDB) GetDishesByRestaurant(resID uint) ([]entities.Dish, error) {
	var dishes []entities.Dish
	result := r.db.Where("res_id = ?", resID).Find(&dishes)
	return dishes, result.Error
}

// Favorite methods
func (r *foodRepositoryDB) GetFavoriteDishesByUser(userID uint) ([]entities.Dish, error) {
	var dishes []entities.Dish
	result := r.db.Joins("JOIN favorite ON favorite.dish_id = dish.dish_id").
		Where("favorite.user_id = ?", userID).Find(&dishes)
	return dishes, result.Error
}

func (r *foodRepositoryDB) AddFavoriteDish(userID uint, dishID uint) error {
    favorite := entities.Favorite{UserID: userID, DishID: dishID}
    return r.db.Create(&favorite).Error
}

func (r *foodRepositoryDB) RemoveFavoriteDish(userID uint, dishID uint) error {
	result := r.db.Where("user_id = ? AND dish_id = ?", userID, dishID).Delete(&entities.Favorite{})
	return result.Error
}

func (r *foodRepositoryDB) IsFavoriteDish(userID uint, dishID uint) (bool, error) {
	var fav entities.Favorite
	result := r.db.Where("user_id = ? AND dish_id = ?", userID, dishID).First(&fav)
	if result.Error != nil {
		if result.Error == gorm.ErrRecordNotFound {
			return false, nil
		}
		return false, result.Error
	}
	return true, nil
}

// Get keywords for a dish (from dish_keyword join table)
func (r *foodRepositoryDB) GetKeywordsByDish(dishID uint) ([]entities.Keyword, error) {
	var keywords []entities.Keyword
	result := r.db.Joins("JOIN dish_keyword ON dish_keyword.keyword_id = keyword.keyword_id").
		Where("dish_keyword.dish_id = ?", dishID).Find(&keywords)
	return keywords, result.Error
}
