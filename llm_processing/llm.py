import os
from openai import OpenAI
from .config import Config

PROMPT_TEMPLATE = """
You are a food review analysis expert. Analyze the restaurant review and extract structured insights for each dish mentioned.

Restaurant Name: {restaurant}

Review:
“{review}”

Rules:
- Extract EACH distinct dish as a SEPARATE object, including dishes in comparisons, lists, or multiple mentions.
- Use the most specific phrase for the dish (e.g., “ลาบเป็ด” over “ลาบ”).
- If a dish is mentioned but has no clear sentiment, include it with empty positive/negative lists.
- Do NOT invent dishes. Avoid generic words like “อาหาร”, “เมนู”, “ของทอด”, “ข้าว”, “food”, “menu” unless followed by a specific named dish.
- Sentiment must be about the dish only (taste, texture, doneness, temperature, presentation). Exclude service/ambience.
- Copy the restaurant name exactly as provided.
- Return RAW JSON only (no commentary).

Fields per dish:
1. dish: specific name that appears verbatim in the review.
2. cuisine: closest cuisine type (e.g., “thai”, “japanese”, “italian”). If ambiguous, use restaurant name as hint; if unclear, use “Others”. Fusion allowed.
3. restriction: one of ["halal", "vegan", "buddhist vegan"] if clearly indicated; otherwise null.
4. sentiment: short keywords/phrases about the dish only, preserving the original language.

Output format (JSON array only):
[
    {{
        "restaurant": <Restaurant Name>,
        "dish": <Dish Name>,
        "cuisine": <Cuisine Type>,
        "restriction": <Restriction Type or null>,
        "sentiment": {{
            "positive": [<positive keywords>],
            "negative": [<negative keywords>]
        }}
    }}
]
"""

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = OpenAI()  # Uses OPENAI_API_KEY from environment
    return _client

def gpt35_extract(restaurant, review):
    client = _get_client()
    prompt = PROMPT_TEMPLATE.format(restaurant=restaurant, review=review)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=700,
    )
    return resp.choices[0].message.content.strip()