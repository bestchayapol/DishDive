# LLM migration plan: Python → Go (SubmitReview path)

This document confirms feasibility and provides a concrete plan to migrate the real‑time SubmitReview pipeline from Python (`llm_processing/single_review.py` + `processor.py`) into the Go backend (`server/`). It includes architecture options, step‑by‑step execution plan, data contracts, environment mapping, risks, rollback, and minimal Go scaffolding.

> Scope: Only the real‑time user review path (SubmitReview). Batch/web review processing can remain in Python. We can keep normalization as‑is initially or port later.

---

## 1) Feasibility summary

- Calls to OpenAI from Go: Supported via official Go SDK (`github.com/openai/openai-go`) or REST via `net/http`. We can instruct the model to return strict JSON matching Go structs to avoid heavy NLP libs.
- DB writes to Postgres from Go: Use `pgx` (recommended) or `database/sql` + `lib/pq`. Upsert into `review_extracts` replicates Python behavior.
- Concurrency/rate limiting: Go has first‑class primitives and `golang.org/x/time/rate`.
- Logging and timeouts: Standard Go context, structured logging.
- Thai heuristics / PyThaiNLP: Optional. We can reduce reliance by designing a stricter JSON schema output from the LLM and light rule checks in Go. If needed later, we can add a small Go ruleset or call a lightweight service.

Conclusion: Migration is fully possible. Complexity is moderate; the critical path is LLM prompt parity and JSON validation.

---

## 2) Current vs target architecture

### Current (real‑time SubmitReview)
1. App → Go: `POST /SubmitReview`.
2. Go persists raw review; spawns Python subprocess: `python -m llm_processing.single_review --restaurant ... --review ...`.
3. Python (LLM + heuristics) writes to `review_extracts` in Postgres.
4. Normalization job maps `review_extracts` → domain tables.

### Target (real‑time SubmitReview, Go‑native)
1. App → Go: `POST /SubmitReview`.
2. Go persists raw review.
3. Go calls OpenAI directly (structured prompt → JSON), validates output, upserts `review_extracts`.
4. Normalization: unchanged initially (still run the existing normalization step), or implement a Go normalizer later.

Feature flag: keep a runtime flag `USE_GO_LLM=1` to switch between Go path and legacy Python subprocess. Rollback: set flag to 0.

---

## 3) Data contracts (unchanged)

`review_extracts` (written by extraction step) — same as today
- `rev_ext_id BIGINT PRIMARY KEY` (could be `BIGSERIAL`),
- `source_id BIGINT` (UserReview ID),
- `source_type VARCHAR(64)` (e.g., `user`),
- `data_extract TEXT` (JSON array of dish objects). 

Dish JSON object (example, align with Python output):
```json
{
  "restaurant_name": "Da Lena",
  "dish_name": "Carbonara",
  "sentiment": "positive",
  "keywords": ["creamy", "bacon"],
  "confidence": 0.86,
  "spans": [{"text": "...", "start": 42, "end": 71}]
}
```
We will validate this structure in Go using typed structs plus lenient decoding (unknown fields ignored).

---

## 4) Environment mapping

Current Python env → Go env:
- DB
  - `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`, `PG_SSLMODE`
- OpenAI
  - `OPENAI_API_KEY`, optional `OPENAI_MODEL` (default from config), rate‑limit knobs
- Control
  - `USE_GO_LLM` (new flag), `PG_WRITE_DISABLED` (optional dev safeguard)

Example Go config mapping:
```go
OPENAI_API_KEY       -> cfg.OpenAI.APIKey
OPENAI_MODEL         -> cfg.OpenAI.Model (default "gpt-4o-mini" or similar)
PG_*                 -> cfg.DB
USE_GO_LLM          -> cfg.LLM.UseGo (bool)
```

---

## 5) Go package layout (proposed)

```
server/
  internal/
    llm/            # OpenAI client, prompts, schema, validation
      client.go
      prompt.go
      schema.go
    extract/        # Orchestrates single-review extraction
      single.go
    repository/
      review_extracts.go  # Upsert logic
    service/
      recommend_service.go  # Wire-in: call extract if USE_GO_LLM
```

---

## 6) Minimal Go scaffolding

### 6.1 OpenAI client and call (Go)
```go
// internal/llm/client.go
package llm

import (
    "context"
    "encoding/json"
    openai "github.com/openai/openai-go"
    "github.com/openai/openai-go/option"
)

type Client struct {
    api *openai.Client
    model string
}

func New(apiKey, model string) *Client {
    if model == "" { model = "gpt-4o-mini" }
    return &Client{
        api: openai.NewClient(option.WithAPIKey(apiKey)),
        model: model,
    }
}
```

```go
// internal/llm/prompt.go
package llm

import (
    "context"
    "encoding/json"
    openai "github.com/openai/openai-go"
)

type Dish struct {
    RestaurantName string   `json:"restaurant_name,omitempty"`
    DishName       string   `json:"dish_name"`
    Sentiment      string   `json:"sentiment,omitempty"`
    Keywords       []string `json:"keywords,omitempty"`
    Confidence     float64  `json:"confidence,omitempty"`
}

type ExtractResponse struct {
    Dishes []Dish `json:"dishes"`
}

const systemPrompt = `You extract dish mentions from a single Thai/English restaurant review.
Return strict JSON only with schema {"dishes": [{"dish_name": string, "sentiment": string, "keywords": [string], "confidence": number}]}. No extra text.`

func (c *Client) Extract(ctx context.Context, restaurant, review string) (*ExtractResponse, error) {
    user := "Restaurant: " + restaurant + "\nReview: " + review
    req := openai.Chat.Completions.NewRequest(
        c.model,
        []openai.ChatCompletionMessageParamUnion{
            openai.SystemMessage(systemPrompt),
            openai.UserMessage(user),
        },
    )
    // Prefer JSON output if supported by SDK
    req.ResponseFormat = openai.ResponseFormatJSONObject()

    resp, err := c.api.Chat.Completions.New(ctx, req)
    if err != nil { return nil, err }
    if len(resp.Choices) == 0 || len(resp.Choices[0].Message.Content) == 0 {
        return &ExtractResponse{Dishes: nil}, nil
    }
    content := resp.Choices[0].Message.Content[0].Text

    var out ExtractResponse
    if err := json.Unmarshal([]byte(content), &out); err != nil {
        return nil, err
    }
    return &out, nil
}
```

### 6.2 Orchestration and upsert
```go
// internal/extract/single.go
package extract

import (
    "context"
    "encoding/json"
    "time"

    "dishdive/server/internal/llm"
    "dishdive/server/internal/repository"
)

type SingleReviewInput struct {
    ReviewID       int64
    RestaurantName string
    ReviewText     string
    SourceType     string // "user"
}

type Service struct {
    LLM  *llm.Client
    Repo *repository.ReviewExtractsRepo
}

func NewService(llmClient *llm.Client, repo *repository.ReviewExtractsRepo) *Service {
    return &Service{LLM: llmClient, Repo: repo}
}

func (s *Service) Run(ctx context.Context, in SingleReviewInput) error {
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    out, err := s.LLM.Extract(ctx, in.RestaurantName, in.ReviewText)
    if err != nil { return err }

    payload, err := json.Marshal(out.Dishes)
    if err != nil { return err }

    return s.Repo.Upsert(ctx, in.SourceType, in.ReviewID, string(payload))
}
```

```go
// internal/repository/review_extracts.go
package repository

import (
    "context"
    "github.com/jackc/pgx/v5/pgxpool"
)

type ReviewExtractsRepo struct { DB *pgxpool.Pool }

func NewReviewExtractsRepo(db *pgxpool.Pool) *ReviewExtractsRepo { return &ReviewExtractsRepo{DB: db} }

func (r *ReviewExtractsRepo) Upsert(ctx context.Context, sourceType string, sourceID int64, dataExtract string) error {
    const q = `
        INSERT INTO review_extracts (source_type, source_id, data_extract)
        VALUES ($1, $2, $3)
        ON CONFLICT (source_type, source_id)
        DO UPDATE SET data_extract = EXCLUDED.data_extract` // idempotent
    _, err := r.DB.Exec(ctx, q, sourceType, sourceID, dataExtract)
    return err
}
```

### 6.3 Wiring into SubmitReview
In `server/internal/service/recommend_service.go` inside the SubmitReview flow:
- Behind `USE_GO_LLM`, call `extractService.Run(ctx, SingleReviewInput{...})` instead of spawning Python.
- Continue logging to `server/logs/` on success/failure.

---

## 7) Step‑by‑step migration plan

1. Config & flag
   - Add `USE_GO_LLM` env + config loader; default `0` (off).
   - Add OpenAI config (API key, model) in Go.
2. DB repository
   - Implement `ReviewExtractsRepo.Upsert()` (idempotent conflict on `(source_type, source_id)`).
3. LLM client
   - Implement `internal/llm` with JSON‑mode prompt and schema.
4. Orchestrator
   - Implement `internal/extract.Service.Run`.
5. Service wiring
   - In SubmitReview, if `USE_GO_LLM==1` then call Go extractor; else spawn Python as today.
6. Observability
   - Log request IDs, durations, LLM tokens (if available), and upsert outcome.
7. Rollout
   - Enable on staging/dev first. Compare JSON outputs vs Python for a sample set.
   - Enable in production gradually; keep rollback by flipping the flag.

---

## 8) Rate limiting & resilience (recommended)
- Add `golang.org/x/time/rate` limiter per‑process (e.g., 2 RPS, burst 4) to protect budgets.
- Add request timeout via context (e.g., 30s).
- Retries: limited retry on transient 5xx from OpenAI.

---

## 9) Normalization (later phase)
- Keep existing normalization scripts initially (no change to consumers).
- If moving normalization to Go:
  - Create `internal/normalize` to transform dish JSON → `dishes`, `review_dishes`, `dish_keywords`, etc.
  - Maintain idempotency by unique keys (e.g., `(source_type, source_id, dish_name)` or canonical IDs).

---

## 10) Risks & mitigations
- Output parity vs Python:
  - Mitigation: adopt strict JSON schema; run A/B on a sample; accept minor differences.
- Thai NLP heuristics missing:
  - Mitigation: rely on LLM JSON with confidence; add lightweight rules; later add a tiny service if required.
- Token cost/runtime surprises:
  - Mitigation: limit prompt length; cache; set rate limits; choose cost‑effective model.
- Secret management:
  - Mitigation: load from env/secret store; avoid committing keys in repo; rotate exposed keys.

---

## 11) Rollback plan
- Keep Python subprocess path intact.
- Controlled by `USE_GO_LLM` env; set to `0` to revert immediately.

---

## 12) Try‑it checklist
- [ ] Add `USE_GO_LLM=1` and `OPENAI_API_KEY` to backend env.
- [ ] Implement `internal/llm`, `internal/extract`, and `repository.ReviewExtractsRepo`.
- [ ] Wire into SubmitReview, build, and run locally against a test DB.
- [ ] Confirm `review_extracts` rows appear and normalization still works.
- [ ] Flip flag off to verify rollback.

---

## 13) Notes
- Keep batch/web review processing in Python for now—no change required.
- When ready, you can later dockerize the Go extractor only; no need to deploy Python for real‑time.
