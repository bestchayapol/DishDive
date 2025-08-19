package handler

import (
    "encoding/json"
    "fmt"
    "net/http"
    "github.com/bestchayapol/DishDive/internal/service"
    "github.com/bestchayapol/DishDive/internal/dtos"
)

type RecommendHandler struct {
    recommendService service.RecommendService
}

func NewRecommendHandler(recommendService service.RecommendService) *RecommendHandler {
    return &RecommendHandler{recommendService: recommendService}
}

// Get preference keywords
func (h *RecommendHandler) GetPreferenceKeywords(w http.ResponseWriter, r *http.Request) {
    userIDStr := r.URL.Query().Get("user_id")
    var userID uint
    _, err := fmt.Sscanf(userIDStr, "%d", &userID)
    if err != nil {
        http.Error(w, "Invalid user_id parameter", http.StatusBadRequest)
        return
    }
    resp, err := h.recommendService.GetPreferenceKeywords(userID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    json.NewEncoder(w).Encode(resp)
}

// Set preference
func (h *RecommendHandler) SetPreference(w http.ResponseWriter, r *http.Request) {
    var req dtos.SetPreferenceRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    userIDStr := r.URL.Query().Get("user_id")
    var userID uint
    _, err := fmt.Sscanf(userIDStr, "%d", &userID)
    if err != nil {
        http.Error(w, "Invalid user_id parameter", http.StatusBadRequest)
        return
    }
    err = h.recommendService.SetPreference(userID, req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.WriteHeader(http.StatusOK)
}

// Get blacklist keywords
func (h *RecommendHandler) GetBlacklistKeywords(w http.ResponseWriter, r *http.Request) {
    userIDStr := r.URL.Query().Get("user_id")
    var userID uint
    _, err := fmt.Sscanf(userIDStr, "%d", &userID)
    if err != nil {
        http.Error(w, "Invalid user_id parameter", http.StatusBadRequest)
        return
    }
    resp, err := h.recommendService.GetBlacklistKeywords(userID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    json.NewEncoder(w).Encode(resp)
}

// Set blacklist
func (h *RecommendHandler) SetBlacklist(w http.ResponseWriter, r *http.Request) {
    var req dtos.SetBlacklistRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    userIDStr := r.URL.Query().Get("user_id")
    var userID uint
    _, err := fmt.Sscanf(userIDStr, "%d", &userID)
    if err != nil {
        http.Error(w, "Invalid user_id parameter", http.StatusBadRequest)
        return
    }
    err = h.recommendService.SetBlacklist(userID, req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.WriteHeader(http.StatusOK)
}

// Get dish review page
func (h *RecommendHandler) GetDishReviewPage(w http.ResponseWriter, r *http.Request) {
    dishIDStr := r.URL.Query().Get("dish_id")
    var dishID uint
    _, err := fmt.Sscanf(dishIDStr, "%d", &dishID)
    if err != nil {
        http.Error(w, "Invalid dish_id parameter", http.StatusBadRequest)
        return
    }
    resp, err := h.recommendService.GetDishReviewPage(dishID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    json.NewEncoder(w).Encode(resp)
}

// Submit review
func (h *RecommendHandler) SubmitReview(w http.ResponseWriter, r *http.Request) {
    var req dtos.SubmitReviewRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    resp, err := h.recommendService.SubmitReview(req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    json.NewEncoder(w).Encode(resp)
}

// Get recommended dishes
func (h *RecommendHandler) GetRecommendedDishes(w http.ResponseWriter, r *http.Request) {
    userIDStr := r.URL.Query().Get("user_id")
    var userID uint
    _, err := fmt.Sscanf(userIDStr, "%d", &userID)
    if err != nil {
        http.Error(w, "Invalid user_id parameter", http.StatusBadRequest)
        return
    }
    resp, err := h.recommendService.GetRecommendedDishes(userID)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    json.NewEncoder(w).Encode(resp)
}