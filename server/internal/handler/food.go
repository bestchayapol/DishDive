package handler

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"strconv"

	"github.com/bestchayapol/DishDive/internal/dtos"
	"github.com/bestchayapol/DishDive/internal/service"
	"github.com/gofiber/fiber/v2"
)

type FoodHandler struct {
	foodService service.FoodService
}

func NewFoodHandler(foodService service.FoodService) *FoodHandler {
	return &FoodHandler{foodService: foodService}
}

// Search restaurants by dish
func (h *FoodHandler) SearchRestaurantsByDish(c *fiber.Ctx) error {
	var req dtos.SearchRestaurantsByDishRequest
	if err := c.BodyParser(&req); err != nil {
		return err
	}
	resp, err := h.foodService.SearchRestaurantsByDish(req)
	if err != nil {
		return err
	}
	return c.JSON(resp)
}

func (h *FoodHandler) GetRestaurantList(c *fiber.Ctx) error {
    resp, err := h.foodService.GetRestaurantList()
    if err != nil {
        return err
    }
    return c.JSON(resp)
}

func (h *FoodHandler) GetRestaurantLocations(c *fiber.Ctx) error {
    // Get resID from path parameter
    resID, err := strconv.Atoi(c.Params("resID"))
    if err != nil {
        return err
    }

    // Get user location from query params
    userLatStr := c.Query("user_lat")
    userLngStr := c.Query("user_lng")
    if userLatStr == "" || userLngStr == "" {
        return fiber.NewError(fiber.StatusBadRequest, "user location required")
    }

    userLat, err := strconv.ParseFloat(userLatStr, 64)
    if err != nil {
        return err
    }
    userLng, err := strconv.ParseFloat(userLngStr, 64)
    if err != nil {
        return err
    }

    resp, err := h.foodService.GetLocationsByRestaurant(uint(resID), userLat, userLng)
    if err != nil {
        return err
    }
    return c.JSON(resp)
}


func (h *FoodHandler) GetDishDetail(c *fiber.Ctx) error {
    dishID, err := strconv.Atoi(c.Params("dishID"))
    if err != nil {
        return err
    }
    
    userID, err := strconv.Atoi(c.Query("userID"))
    if err != nil {
        return err
    }

    resp, err := h.foodService.GetDishDetail(uint(dishID), uint(userID))
    if err != nil {
        return err
    }
    return c.JSON(resp)
}

// Get favorite dishes
func (h *FoodHandler) GetFavoriteDishes(c *fiber.Ctx) error {
	// Get userID from path parameter
	userID, err := strconv.Atoi(c.Params("userID"))
	if err != nil {
		return err
	}

	resp, err := h.foodService.GetFavoriteDishes(uint(userID))
	if err != nil {
		return err
	}
	return c.JSON(resp)
}

// Add these methods to FoodHandler
func (h *FoodHandler) AddFavorite(c *fiber.Ctx) error {
    var req struct {
        UserID uint `json:"user_id"`
        DishID uint `json:"dish_id"`
    }
    if err := c.BodyParser(&req); err != nil {
        return err
    }

    err := h.foodService.AddFavorite(req.UserID, req.DishID)
    if err != nil {
        return err
    }
    return c.SendStatus(fiber.StatusOK)
}

func (h *FoodHandler) RemoveFavorite(c *fiber.Ctx) error {
    var req struct {
        UserID uint `json:"user_id"`
        DishID uint `json:"dish_id"`
    }
    if err := c.BodyParser(&req); err != nil {
        return err
    }
    
    err := h.foodService.RemoveFavorite(req.UserID, req.DishID)
    if err != nil {
        return err
    }
    return c.JSON(map[string]bool{"success": true})
}

// Add or update restaurant location using geocoding API
func (h *FoodHandler) AddOrUpdateLocation(c *fiber.Ctx) error {
	var req dtos.RestaurantLocationResponse
	if err := c.BodyParser(&req); err != nil {
		return err
	}

	// Geocoding logic
	apiKey := os.Getenv("AIzaSyC3PQZPBjTMBOQIkIQaZrEIVuqgMCDm1G8") // Or load from config
	if req.Address != "" {
		lat, lng, err := CallGeocodingAPI(req.Address, apiKey)
		if err != nil {
			return err
		}
		req.Latitude = lat
		req.Longitude = lng
	}

	err := h.foodService.AddOrUpdateLocation(req)
	if err != nil {
		return err
	}

	return c.SendStatus(fiber.StatusOK)
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
