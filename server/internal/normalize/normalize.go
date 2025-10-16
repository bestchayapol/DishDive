package normalize

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/bestchayapol/DishDive/internal/repository"
)

// ExtractItem matches extractor's JSON schema
type ExtractItem struct {
	Restaurant  string  `json:"restaurant"`
	Dish        string  `json:"dish"`
	Cuisine     *string `json:"cuisine"`
	Restriction *string `json:"restriction"`
	Sentiment   struct {
		Positive []string `json:"positive"`
		Negative []string `json:"negative"`
	} `json:"sentiment"`
}

type Service struct {
	Repo  repository.RecommendRepository
	alias map[string]string
}

func NewService(repo repository.RecommendRepository) *Service { return &Service{Repo: repo} }

// Run loads the latest extract JSON for (sourceType, sourceID) and writes normalized rows.
func (s *Service) Run(ctx context.Context, sourceType string, sourceID uint, dishID uint, resID uint) error {
	// Use the provided ctx; caller may add timeout if desired

	// Lazy-load alias map once
	if s.alias == nil {
		if m, err := s.Repo.FetchKeywordAliases(); err == nil {
			s.alias = m
		}
	}

	raw, err := s.Repo.GetLatestReviewExtract(sourceID, sourceType)
	if err != nil {
		return err
	}
	var arr []ExtractItem
	if err := json.Unmarshal([]byte(strings.TrimSpace(raw)), &arr); err != nil {
		// tolerate non-JSON or empty
		return nil
	}
	// Ensure top-level review_dishes entry exists for this review
	rd, err := s.Repo.EnsureReviewDish(sourceID, dishID, resID)
	if err != nil {
		return fmt.Errorf("ensure ReviewDish: %w", err)
	}
	// Attach keywords and update dish keyword frequencies; then recompute rollups
	for _, it := range arr {
		// Positive tokens
		for _, tok := range it.Sentiment.Positive {
			name := strings.TrimSpace(canonicalizeToken(tok, s.alias))
			if name == "" {
				continue
			}
			cat, senti := categorizeKeyword(name, "positive")
			if kw, err := s.Repo.FindOrCreateKeyword(name, cat, senti); err == nil && kw != nil {
				_ = s.Repo.EnsureReviewDishKeyword(rd.RDID, kw.KeywordID)
				_ = s.Repo.BumpDishKeyword(dishID, kw.KeywordID, 1)
			}
		}
		// Negative tokens
		for _, tok := range it.Sentiment.Negative {
			name := strings.TrimSpace(canonicalizeToken(tok, s.alias))
			if name == "" {
				continue
			}
			cat, senti := categorizeKeyword(name, "negative")
			if kw, err := s.Repo.FindOrCreateKeyword(name, cat, senti); err == nil && kw != nil {
				_ = s.Repo.EnsureReviewDishKeyword(rd.RDID, kw.KeywordID)
				_ = s.Repo.BumpDishKeyword(dishID, kw.KeywordID, 1)
			}
		}
	}
	return s.Repo.RecomputeScoresAndRestaurants()
}

// (guessCategory removed — not used)

// Port of Python categorize_keyword for parity
func categorizeKeyword(token string, defaultSentiment string) (category string, sentiment string) {
	t := strings.ToLower(strings.TrimSpace(token))
	if t == "" {
		return "others", defaultSentimentOrNeutral(defaultSentiment)
	}
	costPos := map[string]struct{}{"ถูก": {}, "ไม่แพง": {}, "คุ้ม": {}, "คุ้มค่า": {}, "คุ้มราคา": {}, "ราคาดี": {}, "ราคาถูก": {}, "ราคาคุ้มค่า": {}, "คุ้มจริง": {}, "คุ้มมาก": {}, "ราคาสมเหตุสมผล": {}, "สมราคา": {}}
	costNeg := map[string]struct{}{"แพง": {}, "ราคาแพง": {}, "ไม่คุ้ม": {}, "ไม่คุ้มค่า": {}, "เกินราคา": {}, "ราคาแรง": {}, "แพงไป": {}, "แพงมาก": {}}
	flavorPos := map[string]struct{}{"อร่อย": {}, "ดี": {}, "ดีมาก": {}, "เด็ด": {}, "แซ่บ": {}, "กรอบ": {}, "นุ่ม": {}, "หอม": {}, "เข้มข้น": {}, "สด": {}, "หวาน": {}, "กลมกล่อม": {}, "เด้ง": {}, "ฉ่ำ": {}, "ละมุน": {}, "หอมนุ่ม": {}}
	flavorNeg := map[string]struct{}{"เค็ม": {}, "จืด": {}, "คาว": {}, "เหนียว": {}, "หวานไป": {}, "เผ็ดไป": {}, "ไม่อร่อย": {}, "มันไป": {}, "เลี่ยน": {}, "ไหม้": {}, "ดิบ": {}, "แฉะ": {}}

	if _, ok := costPos[t]; ok {
		return "cost", "positive"
	}
	if _, ok := costNeg[t]; ok {
		return "cost", "negative"
	}
	if _, ok := flavorPos[t]; ok {
		return "flavor", "positive"
	}
	if _, ok := flavorNeg[t]; ok {
		return "flavor", "negative"
	}

	if strings.Contains(t, "ราคา") || strings.Contains(t, "คุ้ม") || strings.Contains(t, "แพง") || strings.Contains(t, "ถูก") {
		// cost with default sentiment if valid else neutral
		ds := defaultSentimentOrNeutral(defaultSentiment)
		return "cost", ds
	}
	ds := defaultSentimentOrNeutral(defaultSentiment)
	return "others", ds
}

func defaultSentimentOrNeutral(s string) string {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "positive", "negative":
		return strings.ToLower(strings.TrimSpace(s))
	default:
		return "neutral"
	}
}

// canonicalizeToken performs Thai-friendly normalization and applies alias map
func canonicalizeToken(raw string, alias map[string]string) string {
	s := strings.TrimSpace(raw)
	if s == "" {
		return s
	}
	// collapse whitespace
	s = strings.Join(strings.Fields(s), " ")
	// best-effort diacritic strip for Thai tone marks (simple subset)
	replacers := []string{
		"\u0E31", "",
		"\u0E34", "",
		"\u0E35", "",
		"\u0E36", "",
		"\u0E37", "",
		"\u0E38", "",
		"\u0E39", "",
		"\u0E47", "",
		"\u0E48", "",
		"\u0E49", "",
		"\u0E4A", "",
		"\u0E4B", "",
		"\u0E4C", "",
		"\u0E4D", "",
		"\u0E4E", "",
	}
	r := strings.NewReplacer(replacers...)
	s = r.Replace(s)
	low := strings.ToLower(s)
	if base, ok := alias[low]; ok {
		return base
	}
	return s
}

