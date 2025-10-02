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
	// Optional normalized English selections; when provided, server will expand them
	FlavorENPreferred   []string `json:"flavor_en_preferred,omitempty"`
	CostENPreferred     []string `json:"cost_en_preferred,omitempty"`
	FlavorENBlacklisted []string `json:"flavor_en_blacklisted,omitempty"`
	CostENBlacklisted   []string `json:"cost_en_blacklisted,omitempty"`
}

type KeywordSettingUpdate struct {
	KeywordID       uint    `json:"keyword_id"`
	PreferenceValue float64 `json:"preference_value"`
	BlacklistValue  float64 `json:"blacklist_value"`
}

type UserSettingsResponse struct {
	Keywords []KeywordSettingResponse `json:"keywords"`
	// Optional normalized selections (English UI options mapped on server)
	FlavorENPreferred   []string `json:"flavor_en_preferred,omitempty"`
	CostENPreferred     []string `json:"cost_en_preferred,omitempty"`
	FlavorENBlacklisted []string `json:"flavor_en_blacklisted,omitempty"`
	CostENBlacklisted   []string `json:"cost_en_blacklisted,omitempty"`
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
	Success  bool  `json:"success"`
	ReviewID *uint `json:"review_id,omitempty"`
}

type ReviewExtractStatusResponse struct {
	ReviewID   uint   `json:"review_id"`
	SourceType string `json:"source_type"`
	Found      bool   `json:"found"`
}
