package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"
)

type Client struct {
	httpClient *http.Client
	apiKey     string
	model      string
}

func NewClientFromEnv() *Client {
	apiKey := os.Getenv("OPENAI_API_KEY")
	model := os.Getenv("OPENAI_MODEL")
	if model == "" {
		model = "gpt-4o-mini"
	}
	return &Client{
		httpClient: &http.Client{Timeout: 35 * time.Second},
		apiKey:     apiKey,
		model:      model,
	}
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type chatRequest struct {
	Model          string            `json:"model"`
	Messages       []Message         `json:"messages"`
	ResponseFormat map[string]string `json:"response_format,omitempty"`
}

type chatResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

type Dish struct {
	RestaurantName string   `json:"restaurant_name,omitempty"`
	DishName       string   `json:"dish_name"`
	Sentiment      string   `json:"sentiment,omitempty"`
	Keywords       []string `json:"keywords,omitempty"`
	Confidence     float64  `json:"confidence,omitempty"`
}

type ExtractResponse struct {
	Items []ExtractItem `json:"items"`
}

// Python-parity schema expected by normalization and legacy data
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

const systemPrompt = `You are an extraction engine for Thai restaurant reviews.

TASK: Return an array (raw JSON only) of dish objects for this single review.

Restaurant: {restaurant}
Review: "{review}"

RULES (concise):
1. Split multiple dishes joined by และ, กับ, และก็, หรือ, ,
2. Use most specific phrase.
3. Keep dish if mentioned even without sentiment (empty lists allowed).
4. Sentiment lists: taste / texture / doneness / temperature / presentation only.
5. A valid dish must include an ingredient/prep root from this set OR be a known multi-word dish (e.g., ปลาหมึกนึ่งมะนาว, ข้าวผัดกุ้ง, กุ้งเผา, ยำวุ้นเส้นรวมมิตร, กุ้งซอสมะขาม).
6. DO NOT output generic placeholders like เมนูรวม/อาหาร/เมนู or quality/ambience/price words alone (e.g., อร่อย, บรรยากาศดี, ราคาไม่แพง, คุ้มค่า, สะอาด, สด, เด็ด, แซ่บ) unless attached to a valid dish root.
7. If no valid dish is present, return [] exactly.
8. Ignore phrases starting with อาหาร / เมนู lacking a valid root.
9. Copy restaurant name exactly in every object.
10. cuisine: choose from [thai,chinese,japanese,korean,italian,american,vietnamese,indian,mexican,fusion,others].
11. restriction: one of ["halal","vegan","buddhist vegan", null].

Schema:
[
  {
    "restaurant": "…",
    "dish": "…",
    "cuisine": "…",
    "restriction": null,
    "sentiment": {"positive":[],"negative":[]}
  }
]

Return ONLY the JSON array.`

// Forbidden/generic dish placeholders we must avoid keeping
var forbiddenDishes = map[string]struct{}{
	"เมนูรวม": {}, "เมนูต่างๆ": {}, "อาหารรวม": {}, "assorted": {}, "อาหาร": {}, "เมนู": {},
}

// Ingredient roots (subset; expand as needed to match Python INGREDIENT_ROOTS)
var ingredientRoots = []string{
	"ต้มยำ", "ลาบ", "ส้มตำ", "ก้อย", "ผัด", "แกง", "เกี๊ยวซ่า", "เกี๊ยว",
	"เต้าหู้", "ปลาหมึก", "ปลากระพง", "คอหมูย่าง", "หมูย่าง", "ไก่ทอด", "ปีกไก่",
	"กระดูกหมู", "ผัดไทย", "กะเพรา", "กะเพร", "ข้าวผัด", "ปลาเผา", "ยำ",
}

var rbMethods = []string{"ทอด", "ผัด", "ย่าง", "นึ่ง", "ต้ม", "แกง", "เผา", "อบ"}
var rbFlavorParts = []string{"มะนาว", "กระเทียม", "พริก", "ปลาร้า", "สมุนไพร"}
var rbPositive = []string{"อร่อย", "แซ่บ", "เด็ด", "ดี", "หอม", "กรอบ", "เข้มข้น", "สด", "นุ่ม", "หวาน", "กลมกล่อม"}
var rbNegative = []string{"เค็ม", "จืด", "เหนียว", "มันไป", "หวานไป", "เผ็ดไป", "ไม่อร่อย", "คาว"}

var dishRegex = regexp.MustCompile(`(ต้มยำ|ลาบ|ส้มตำ|ก้อย|ผัด|แกง|เกี๊ยวซ่า|เกี๊ยว|เต้าหู้|ปลาหมึก|ปลากระพง|คอหมูย่าง|หมูย่าง|ไก่ทอด|ปีกไก่|กระดูกหมู|ผัดไทย|กะเพรา|กะเพร|ข้าวผัด|ปลาเผา|ยำ)`)

func (c *Client) Extract(ctx context.Context, restaurant, review string, hintDish string) (*ExtractResponse, error) {
	if c.apiKey == "" {
		return &ExtractResponse{Items: nil}, nil
	}
	if hintDish != "" {
		review = "(dish mentioned: " + hintDish + ") " + review
	}
	user := "Restaurant: " + restaurant + "\nReview: " + review

	reqBody := chatRequest{
		Model: c.model,
		Messages: []Message{
				{Role: "system", Content: systemPrompt},
				{Role: "user", Content: user},
			},
			ResponseFormat: map[string]string{"type": "json_object"},
		}
	data, _ := json.Marshal(reqBody)
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, "https://api.openai.com/v1/chat/completions", bytes.NewReader(data))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, errors.New("openai request failed: " + resp.Status)
	}
	var ch chatResponse
	if err := json.NewDecoder(resp.Body).Decode(&ch); err != nil {
		return nil, err
	}
	if len(ch.Choices) == 0 || ch.Choices[0].Message.Content == "" {
		// No content; try rule-based fallback
		items := ruleBasedExtract(restaurant, review)
		return &ExtractResponse{Items: items}, nil
	}
	// Parse response robustly and decide if fallback is needed
	arr, ok := safeParseToArray(ch.Choices[0].Message.Content)
	if !ok || needsFallback(arr, review) {
		items := ruleBasedExtract(restaurant, review)
		// If a hint dish is present and rule-based returned at least one, override first dish name
		if hintDish != "" && len(items) > 0 {
			items[0].Dish = hintDish
		}
		return &ExtractResponse{Items: items}, nil
	}
	return &ExtractResponse{Items: arr}, nil
}

// safeParseToArray attempts to find and parse a JSON array within raw content
func safeParseToArray(raw string) ([]ExtractItem, bool) {
	s := strings.TrimSpace(raw)
	if s == "" {
		return nil, false
	}
	// Try direct array first
	var arr []ExtractItem
	if err := json.Unmarshal([]byte(s), &arr); err == nil {
		return arr, true
	}
	// Try to extract substring between first '[' and last ']'
	i := strings.Index(s, "[")
	j := strings.LastIndex(s, "]")
	if i >= 0 && j > i {
		snip := s[i : j+1]
		if err := json.Unmarshal([]byte(snip), &arr); err == nil {
			return arr, true
		}
	}
	// Try object with items field
	var wrapper struct {
		Items []ExtractItem `json:"items"`
	}
	if err := json.Unmarshal([]byte(s), &wrapper); err == nil && len(wrapper.Items) >= 0 {
		return wrapper.Items, true
	}
	return nil, false
}

func needsFallback(arr []ExtractItem, review string) bool {
	if len(arr) == 0 {
		// if the review clearly mentions dish tokens, try to synthesize
		if dishRegex.FindStringIndex(review) != nil {
			return true
		}
		return true
	}
	allForbidden := true
	for _, it := range arr {
		d := strings.TrimSpace(it.Dish)
		if d == "" {
			continue
		}
		if _, bad := forbiddenDishes[d]; !bad {
			allForbidden = false
		}
	}
	return allForbidden
}

func ruleBasedExtract(restaurant, review string) []ExtractItem {
	// Collect candidate dishes by scanning for ingredient roots and optional method/flavor parts after
	type void = struct{}
	candidates := map[string]void{}
	// Thai is case-insensitive; operate on original string
	// Build candidates by scanning occurrences of each ingredient root
	for _, ing := range ingredientRoots {
		idx := 0
		for {
			k := strings.Index(review[idx:], ing)
			if k < 0 {
				break
			}
			start := idx + k
			tail := review[start+len(ing):]
			// take first few tokens after the ingredient
			extra := []string{}
			parts := strings.Fields(tail)
			for _, p := range parts {
				p = strings.Trim(p, ".,!?:;\"\t")
				if p == "" {
					continue
				}
				if startsWithAny(p, rbMethods) || startsWithAny(p, rbFlavorParts) {
					extra = append(extra, p)
					if len(extra) >= 3 {
						break
					}
				} else {
					break
				}
			}
			phrase := ing + strings.Join(extra, "")
			// trim trailing sentiments glued
			for _, s := range append(rbPositive, rbNegative...) {
				// TrimSuffix is a no-op if the suffix isn't present, so no need to check HasSuffix
				phrase = strings.TrimSuffix(phrase, s)
			}
			phrase = strings.TrimSpace(phrase)
			if phrase != "" {
				if _, bad := forbiddenDishes[phrase]; !bad {
					candidates[phrase] = void{}
				}
			}
			idx = start + len(ing)
			if idx >= len(review) {
				break
			}
		}
	}
	if len(candidates) == 0 {
		// fallback to bare ingredients present
		for _, ing := range ingredientRoots {
			if strings.Contains(review, ing) {
				if _, bad := forbiddenDishes[ing]; !bad {
					candidates[ing] = void{}
				}
			}
		}
	}
	// sentiment window within 40 chars after occurrence of each candidate
	items := []ExtractItem{}
	for dish := range candidates {
		pos := []string{}
		neg := []string{}
		// naive scan: capture tokens within 40 chars after any occurrence
		idx := 0
		for {
			k := strings.Index(review[idx:], dish)
			if k < 0 {
				break
			}
			start := idx + k + len(dish)
			window := review[start:]
			if len(window) > 40 {
				window = window[:40]
			}
			for _, t := range rbPositive {
				if strings.Contains(window, t) && !contains(pos, t) {
					pos = append(pos, t)
				}
			}
			for _, t := range rbNegative {
				if strings.Contains(window, t) && !contains(neg, t) {
					neg = append(neg, t)
				}
			}
			idx = start
			if idx >= len(review) {
				break
			}
		}
		it := ExtractItem{Restaurant: restaurant, Dish: dish}
		it.Sentiment.Positive = pos
		it.Sentiment.Negative = neg
		cuisine := "thai"
		it.Cuisine = &cuisine
		// restriction defaults to nil
		items = append(items, it)
	}
	return items
}

func startsWithAny(s string, arr []string) bool {
	for _, p := range arr {
		if strings.HasPrefix(s, p) {
			return true
		}
	}
	return false
}

func contains(arr []string, v string) bool {
	for _, x := range arr {
		if x == v {
			return true
		}
	}
	return false
}
