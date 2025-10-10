package repository

import (
	"github.com/bestchayapol/DishDive/internal/config"
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
	// Only return definite locations: coords present and non-zero, and not the known default centroid
	result := r.db.Where(
		"res_id = ? AND latitude IS NOT NULL AND longitude IS NOT NULL AND latitude <> 0 AND longitude <> 0 AND NOT (latitude = ? AND longitude = ?)",
		resID, 15.870032, 100.992541,
	).Find(&locations)
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
	// Only include restaurants that have at least one definite location AND are in the whitelist
	result := r.db.Model(&entities.Restaurant{}).
		Select("DISTINCT restaurants.*").
		Joins("JOIN restaurant_locations rl ON rl.res_id = restaurants.res_id").
		Where("rl.latitude IS NOT NULL AND rl.longitude IS NOT NULL AND rl.latitude <> 0 AND rl.longitude <> 0 AND NOT (rl.latitude = ? AND rl.longitude = ?)", 15.870032, 100.992541).
		Where("restaurants.res_name IN ?", config.WhitelistedRestaurants).
		Find(&restaurants)
	return restaurants, result.Error
}

func (r *foodRepositoryDB) GetRestaurantByID(resID uint) (*entities.Restaurant, error) {
	var restaurant entities.Restaurant
	result := r.db.Where("res_id = ? AND res_name IN ?", resID, config.WhitelistedRestaurants).First(&restaurant)
	if result.Error != nil {
		return nil, result.Error
	}
	return &restaurant, nil
}

func (r *foodRepositoryDB) SearchRestaurantsByDish(dishName string, latitude, longitude, radius float64) ([]entities.Restaurant, error) {
	var restaurants []entities.Restaurant
	// Join dishes and filter by dish name, location, and whitelist
	result := r.db.Model(&entities.Restaurant{}).
		Select("DISTINCT restaurants.*").
		Joins("JOIN dishes ON dishes.res_id = restaurants.res_id").
		Joins("JOIN restaurant_locations rl ON rl.res_id = restaurants.res_id").
		Where("dishes.dish_name LIKE ?", "%"+dishName+"%").
		Where("rl.latitude IS NOT NULL AND rl.longitude IS NOT NULL AND rl.latitude <> 0 and rl.longitude <> 0 AND NOT (rl.latitude = ? AND rl.longitude = ?)", 15.870032, 100.992541).
		Where("restaurants.res_name IN ?", config.WhitelistedRestaurants).
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
	result := r.db.Joins("JOIN favorites ON favorites.dish_id = dishes.dish_id").
		Where("favorites.user_id = ?", userID).Find(&dishes)
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
	result := r.db.Joins("JOIN dish_keywords ON dish_keywords.keyword_id = keywords.keyword_id").
		Where("dish_keywords.dish_id = ?", dishID).Find(&keywords)
	return keywords, result.Error
}

// Get prominent flavor for a dish (highest frequency flavor keyword)
func (r *foodRepositoryDB) GetProminentFlavorByDish(dishID uint) (*string, error) {
	var result struct {
		Keyword string `json:"keyword"`
	}

	query := `
		SELECT k.keyword
		FROM keywords k
		JOIN dish_keywords dk ON k.keyword_id = dk.keyword_id
		WHERE dk.dish_id = ? AND LOWER(k.category) = 'flavor'
		ORDER BY dk.frequency DESC
		LIMIT 1
	`

	err := r.db.Raw(query, dishID).Scan(&result).Error
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			return nil, nil // No flavor found
		}
		return nil, err
	}

	if result.Keyword == "" {
		return nil, nil
	}

	return &result.Keyword, nil
}


// Try cuisine + tag first, then cuisine default
func (r *foodRepositoryDB) GetCuisineImageByCuisineAndTag(cuisine string, imageTag *string) (string, error) {
	var img entities.CuisineImage
	// Try with tag if provided
	if imageTag != nil && *imageTag != "" {
		res := r.db.Joins("JOIN keywords ON keywords.keyword_id = cuisine_images.keyword_id").
			Where("LOWER(keywords.keyword) = LOWER(?) AND cuisine_images.image_tag = ?", cuisine, *imageTag).
			First(&img)
		if res.Error == nil && img.CuisineImageURL != "" {
			return img.CuisineImageURL, nil
		}
	}
	// Fallback to cuisine-only (image_tag NULL)
	res := r.db.Joins("JOIN keywords ON keywords.keyword_id = cuisine_images.keyword_id").
		Where("LOWER(keywords.keyword) = LOWER(?) AND cuisine_images.image_tag IS NULL", cuisine).
		First(&img)
	if res.Error != nil {
		if res.Error == gorm.ErrRecordNotFound {
			return "", nil
		}
		return "", res.Error
	}
	return img.CuisineImageURL, nil
}

// Get top keywords for a dish with their frequencies, ordered by frequency
func (r *foodRepositoryDB) GetTopKeywordsByDishWithFrequency(dishID uint) ([]DishKeywordWithFrequency, error) {
	var results []DishKeywordWithFrequency

	err := r.db.Raw(`
		SELECT k.keyword, k.category, dk.frequency 
		FROM keywords k 
		JOIN dish_keywords dk ON k.keyword_id = dk.keyword_id 
		WHERE dk.dish_id = ? 
		ORDER BY dk.frequency DESC
	`, dishID).Scan(&results).Error

	return results, err
}

// Get review counts for a dish (using actual database values)
func (r *foodRepositoryDB) GetReviewCountsByDish(dishID uint) (positiveReviews int, totalReviews int, err error) {
	// Get the dish to access its scores from the database
	var dish entities.Dish
	err = r.db.Where("dish_id = ?", dishID).First(&dish).Error
	if err != nil {
		return 0, 0, err
	}

	// Use the actual positive and negative scores from the database
	positiveReviews = dish.PositiveScore
	negativeReviews := dish.NegativeScore
	totalReviews = positiveReviews + negativeReviews

	// Ensure we have valid data
	if totalReviews == 0 {
		return 0, 0, nil // Return 0 if no reviews
	}

	return positiveReviews, totalReviews, nil
}
