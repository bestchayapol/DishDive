package dtos

type RestaurantListItemResponse struct {
	ResID     uint    `json:"res_id"`
	ResName   string  `json:"res_name"`
	ImageLink *string `json:"image_link,omitempty"`
	Cuisine   *string `json:"cuisine,omitempty"`
	Locations    []RestaurantLocationResponse `json:"locations"` // Distance from user, if calculated
}

type SearchRestaurantsByDishRequest struct {
	DishName string `json:"dish_name"`
	Latitude float64 `json:"latitude,omitempty"` // User location for distance filtering
	Longitude float64 `json:"longitude,omitempty"`
	Radius   float64 `json:"radius,omitempty"` // Search radius in km
}

type SearchRestaurantsByDishResponse struct {
	ResID     uint    `json:"res_id"`
	ResName   string  `json:"res_name"`
	ImageLink *string `json:"image_link,omitempty"`
	Cuisine   *string `json:"cuisine,omitempty"`
	Location     RestaurantLocationResponse `json:"location"` // The matched branch/location
	Distance     float64 `json:"distance,omitempty"` // Distance from user, if calculated
}

type RestaurantLocationResponse struct {
	RLID         uint    `json:"rl_id"`
	LocationName string  `json:"location_name"`
	Address      string  `json:"address,omitempty"`
	Latitude     float64 `json:"latitude"`
	Longitude    float64 `json:"longitude"`
	Distance     float64 `json:"distance,omitempty"` // Distance from user, if calculated
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