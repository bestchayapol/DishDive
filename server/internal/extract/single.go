package extract

import (
	"context"
	"encoding/json"
	"time"

	"github.com/bestchayapol/DishDive/internal/llm"
	"github.com/bestchayapol/DishDive/internal/repository"
)

type SingleReviewInput struct {
	ReviewID       uint
	RestaurantName string
	ReviewText     string
	SourceType     string // e.g., "user"
	HintDish       string // optional dish hint from the selected dish
	KnownCuisine   *string
	KnownRestrict  *string
}

type Service struct {
	LLM  *llm.Client
	Repo repository.RecommendRepository
}

func NewService(llmClient *llm.Client, repo repository.RecommendRepository) *Service {
	return &Service{LLM: llmClient, Repo: repo}
}

func (s *Service) Run(ctx context.Context, in SingleReviewInput) error {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	out, err := s.LLM.Extract(ctx, in.RestaurantName, in.ReviewText, in.HintDish)
	if err != nil {
		return err
	}
	// Inherit cuisine/restriction from the selected dish if known
	if out != nil && len(out.Items) > 0 {
		for i := range out.Items {
			if in.KnownCuisine != nil { out.Items[i].Cuisine = in.KnownCuisine }
			if in.KnownRestrict != nil { out.Items[i].Restriction = in.KnownRestrict }
		}
	}
	// Persist exactly what the normalizer (and previous Python pipeline) expects: an array
	payload, _ := json.Marshal(out.Items)
	return s.Repo.UpsertReviewExtract(uint(in.ReviewID), in.SourceType, string(payload))
}
