package dtos

// Unified Settings DTOs
type KeywordSettingResponse struct {
	KeywordID       uint    `json:"keyword_id"`
	Keyword         string  `json:"keyword"`
	Category        string  `json:"category"`
	PreferenceValue float64 `json:"preference_value"` // 0.0-1.0, 0 means not preferred
	BlacklistValue  float64 `json:"blacklist_value"`  // 0.0-1.0, 0 means not blacklisted
	IsPreferred     bool    `json:"is_preferred"`     // convenience field: preference_value > 0
	IsBlacklisted   bool    `json:"is_blacklisted"`   // convenience field: blacklist_value > 0
}

type BulkUpdateSettingsRequest struct {
	Settings []KeywordSettingUpdate `json:"settings"`
}

type KeywordSettingUpdate struct {
	KeywordID       uint    `json:"keyword_id"`
	PreferenceValue float64 `json:"preference_value"`
	BlacklistValue  float64 `json:"blacklist_value"`
}

type UserSettingsResponse struct {
	Keywords []KeywordSettingResponse `json:"keywords"`
}

// Review DTOs
type DishReviewPageResponse struct {
	DishID    uint    `json:"dish_id"`
	DishName  string  `json:"dish_name"`
	ImageLink *string `json:"image_link,omitempty"`
	ResID     uint    `json:"res_id"`
	ResName   string  `json:"res_name"`
}

type SubmitReviewRequest struct {
	DishID     uint   `json:"dish_id"`
	ResID      uint   `json:"res_id"`
	UserID     uint   `json:"user_id"`
	ReviewText string `json:"review_text"`
}

type SubmitReviewResponse struct {
	Success bool `json:"success"`
}
