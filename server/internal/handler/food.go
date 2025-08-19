package handler

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/service"
)

type FoodHandler struct {
	foodService service.FoodService
}

func NewFoodHandler(foodService service.FoodService) *FoodHandler {
	return &FoodHandler{foodService: foodService}
}

// Search restaurants by dish
func (h *FoodHandler) SearchRestaurantsByDish(w http.ResponseWriter, r *http.Request) {
	var req dtos.SearchRestaurantsByDishRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	resp, err := h.foodService.SearchRestaurantsByDish(req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(resp)
}

// Get restaurant menu
func (h *FoodHandler) GetRestaurantMenu(w http.ResponseWriter, r *http.Request) {
	// Get resID from query param
	resIDStr := r.URL.Query().Get("res_id")
	if resIDStr == "" {
		http.Error(w, "Missing res_id parameter", http.StatusBadRequest)
		return
	}
	var resID uint
	_, err := fmt.Sscanf(resIDStr, "%d", &resID)
	if err != nil {
		http.Error(w, "Invalid res_id parameter", http.StatusBadRequest)
		return
	}
	userLatStr := r.URL.Query().Get("user_lat")
	userLngStr := r.URL.Query().Get("user_lng")
	if resIDStr == "" || userLatStr == "" || userLngStr == "" {
		http.Error(w, "Missing res_id or user location parameters", http.StatusBadRequest)
		return
	}
	var userLat, userLng float64
	_, err = fmt.Sscanf(userLatStr, "%f", &userLat)
	if err != nil {
		http.Error(w, "Invalid user_lat parameter", http.StatusBadRequest)
		return
	}
	_, err = fmt.Sscanf(userLngStr, "%f", &userLng)
	if err != nil {
		http.Error(w, "Invalid user_lng parameter", http.StatusBadRequest)
		return
	}
	resp, err := h.foodService.GetLocationsByRestaurant(resID, userLat, userLng)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(resp)
}

// Get favorite dishes
func (h *FoodHandler) GetFavoriteDishes(w http.ResponseWriter, r *http.Request) {
	// Get userID from query param (or context/session in real app)
	userIDStr := r.URL.Query().Get("user_id")
	if userIDStr == "" {
		http.Error(w, "Missing user_id parameter", http.StatusBadRequest)
		return
	}
	var userID uint
	_, err := fmt.Sscanf(userIDStr, "%d", &userID)
	if err != nil {
		http.Error(w, "Invalid user_id parameter", http.StatusBadRequest)
		return
	}
	resp, err := h.foodService.GetFavoriteDishes(userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(resp)
}

// Add or update restaurant location using geocoding API
func (h *FoodHandler) AddOrUpdateLocation(w http.ResponseWriter, r *http.Request) {
	var req dtos.RestaurantLocationResponse
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	// Geocoding logic
	apiKey := os.Getenv("AIzaSyC3PQZPBjTMBOQIkIQaZrEIVuqgMCDm1G8") // Or load from config
	if req.Address != "" {
		lat, lng, err := CallGeocodingAPI(req.Address, apiKey)
		if err != nil {
			http.Error(w, "Geocoding failed: "+err.Error(), http.StatusBadRequest)
			return
		}
		req.Latitude = lat
		req.Longitude = lng
	}
	err := h.foodService.AddOrUpdateLocation(req)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
}

// Example function to call Google Geocoding API (pseudo-code)
func CallGeocodingAPI(address, apiKey string) (float64, float64, error) {
	endpoint := "https://maps.googleapis.com/maps/api/geocode/json"
	u := fmt.Sprintf("%s?address=%s&key=%s", endpoint, url.QueryEscape(address), apiKey)
	resp, err := http.Get(u)
	if err != nil {
		return 0, 0, err
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return 0, 0, err
	}
	var result struct {
		Results []struct {
			Geometry struct {
				Location struct {
					Lat float64 `json:"lat"`
					Lng float64 `json:"lng"`
				} `json:"location"`
			} `json:"geometry"`
		} `json:"results"`
		Status string `json:"status"`
	}
	if err := json.Unmarshal(body, &result); err != nil {
		return 0, 0, err
	}
	if result.Status != "OK" || len(result.Results) == 0 {
		return 0, 0, fmt.Errorf("no results found for address")
	}
	lat := result.Results[0].Geometry.Location.Lat
	lng := result.Results[0].Geometry.Location.Lng
	return lat, lng, nil
}
