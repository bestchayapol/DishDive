package dtos

type RestaurantListItemResponse struct {
	ResID     uint    `json:"res_id"`
	ResName   string  `json:"res_name"`
	ImageLink *string `json:"image_link,omitempty"`
	Cuisine   *string `json:"cuisine,omitempty"`
	// Distance  float64 `json:"distance,omitempty"` 
}

type SearchRestaurantsByDishRequest struct {
	DishName string `json:"dish_name"`
}

type SearchRestaurantsByDishResponse struct {
	ResID     uint    `json:"res_id"`
	ResName   string  `json:"res_name"`
	ImageLink *string `json:"image_link,omitempty"`
	Cuisine   *string `json:"cuisine,omitempty"`
	// Distance  float64 `json:"distance,omitempty"` 
}

type FavoriteDishResponse struct {
	DishID          uint    `json:"dish_id"`
	DishName        string  `json:"dish_name"`
	ImageLink       *string `json:"image_link,omitempty"`
	SentimentScore  float64 `json:"sentiment_score"`
	Cuisine         *string `json:"cuisine,omitempty"`
	ProminentFlavor *string `json:"prominent_flavor,omitempty"`
}

type RemoveFavoriteRequest struct {
	DishID uint `json:"dish_id"`
}

type RemoveFavoriteResponse struct {
	Success bool `json:"success"`
}

type RestaurantMenuItemResponse struct {
	DishID          uint    `json:"dish_id"`
	DishName        string  `json:"dish_name"`
	ImageLink       *string `json:"image_link,omitempty"`
	SentimentScore  float64 `json:"sentiment_score"`
	Cuisine         *string `json:"cuisine,omitempty"`
	ProminentFlavor *string `json:"prominent_flavor,omitempty"`
	IsFavorite      bool    `json:"is_favorite"`
}

type DishDetailResponse struct {
	DishID          uint                `json:"dish_id"`
	DishName        string              `json:"dish_name"`
	ImageLink       *string             `json:"image_link,omitempty"`
	SentimentScore  float64             `json:"sentiment_score"`
	Cuisine         *string             `json:"cuisine,omitempty"`
	ProminentFlavor *string             `json:"prominent_flavor,omitempty"`
	TopKeywords     map[string][]string `json:"top_keywords"` // e.g. {"taste": [...], "cost": [...], "general": [...]}
	IsFavorite      bool                `json:"is_favorite"`
}