import os
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from .config import Config

PROMPT = PromptTemplate.from_template(
    """
You are a food review analysis expert specialized in Thai cuisine. Your task is to analyze a Thai restaurant review and extract structured insights for each dish mentioned.

Restaurant Name: {restaurant}

Review:
“{review}”

Please extract and return the following information for each food dish found in the review:

1. Dish Name: Clearly identify the name of the dish being reviewed (e.g., "ต้มยำกุ้ง", "ข้าวผัด", "คอหมูย่าง"). There can be more than one dish per review.
2. Cuisine: Identify the closest matching cuisine for a dish (ต้มยำกุ้ง is "thai", pizza is "italian"). Check the dish name first; if that's ambiguous (e.g., steak), use the restaurant name as a hint. If still unclear, set to "Others". Only one cuisine per dish; use "Fusion" for fusion dishes.
3. Restrictions: Identify potential restrictions of a dish ("halal", "vegan", "thai buddhist vegan"). If none are detected, set to null. Consider both the dish name and the restaurant name, but do not assume restrictions that contradict the dish.
4. Sentiment (STRICT, VERBATIM):
     - Extract only attribute-specific keywords about the dish (taste, texture, temperature, presentation, special characteristics).
     - Positive/negative lists must contain ONLY exact words or phrases that appear in the review text, verbatim (no synonyms, no paraphrases, no inferred intensifiers).
     - Do NOT upgrade/soften intensity (e.g., if the review says "อร่อย" do NOT output "อร่อยมาก" unless the word "มาก" actually appears).
     - If a keyword does not refer to a dish (e.g., general service/price/ambience like "บริการดี", "ราคาไม่แพง"), ignore it for sentiment.
     - If no dish-specific sentiment is present, use an empty list.

General rules:
- If no explicit dish/menu item name is found in the review, return an empty JSON array [] (no text, just []).
- If the review mentions only generic words like "อาหาร", "เมนู", "ฟู้ด", or ratings like "food: 4" without naming a specific dish/menu item, return an empty JSON array [] (no text, just []).
- Dish must be a non-empty string. Never output null, empty string, or placeholders (e.g., "-", "N/A"). If you cannot identify a specific dish name, return nothing (no output).
- Return raw JSON only; do not include explanations or comments.

Output Format (JSON array):
[
    {{
        "review_id":  <Review ID>,
        "restaurant": <Restaurant Name>,
        "dish": <Dish Name>,
        "cuisine":  <Cuisine Type>,
        "restriction":  <Restriction Type>,
        "sentiment": {{
            "positive":  ["..."],
            "negative":  ["..."]
        }}
    }}
]

Do not include any explanation, reasoning, Markdown, or comments — only return raw JSON that closes all brackets/braces (or return nothing when instructed).
"""
)


def build_llm(cfg: Config) -> OllamaLLM:
    return OllamaLLM(
        model=cfg.ollama_model,
        base_url=cfg.ollama_base_url,
        num_ctx=cfg.ollama_num_ctx,
        num_predict=cfg.ollama_num_predict,
        temperature=cfg.ollama_temperature,
        top_p=cfg.ollama_top_p,
        repeat_penalty=cfg.ollama_repeat_penalty,
        num_thread=cfg.ollama_threads,
        **({"format": "json"} if cfg.ollama_json_mode else {}),
    )


def build_chain(cfg: Config):
    llm = build_llm(cfg)
    chain = PROMPT | llm
    return llm, chain
