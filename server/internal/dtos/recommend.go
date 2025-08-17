package dtos

type PreferenceKeywordResponse struct {
	KeywordID         uint    `json:"keyword_id"`
	Keyword           string  `json:"keyword"`
	Category          string  `json:"category"`
	IsPreferred       bool    `json:"is_preferred"`
	SentimentThreshold float64 `json:"sentiment_threshold"`
}

type SetPreferenceRequest struct {
	KeywordID         uint    `json:"keyword_id"`
	IsPreferred       bool    `json:"is_preferred"`
	SentimentThreshold float64 `json:"sentiment_threshold"`
}

type BlacklistKeywordResponse struct {
	KeywordID         uint    `json:"keyword_id"`
	Keyword           string  `json:"keyword"`
	Category          string  `json:"category"`
	IsBlacklisted     bool    `json:"is_blacklisted"`
	SentimentThreshold float64 `json:"sentiment_threshold"`
}

type SetBlacklistRequest struct {
	KeywordID         uint    `json:"keyword_id"`
	IsBlacklisted     bool    `json:"is_blacklisted"`
	SentimentThreshold float64 `json:"sentiment_threshold"`
}

type DishReviewPageResponse struct {
	DishID     uint    `json:"dish_id"`
	DishName   string  `json:"dish_name"`
	ImageLink  *string `json:"image_link,omitempty"`
	ResID      uint    `json:"res_id"`
	ResName    string  `json:"res_name"`
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
