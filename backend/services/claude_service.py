"""
AI Service — powered by Google Gemini (free tier).
Uses gemini-2.0-flash for all chat, extraction, and generation tasks.
"""
import google.generativeai as genai
from backend.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

_model = genai.GenerativeModel("gemini-2.5-flash")


def _call(prompt: str, max_tokens: int = 1024) -> str:
    try:
        response = _model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            ),
        )
        return response.text.strip()
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            raise RuntimeError(
                "Gemini API quota exceeded. Get a new free API key at https://aistudio.google.com/apikey "
                "and update GEMINI_API_KEY in your .env file."
            )
        if "404" in err or "not found" in err.lower():
            raise RuntimeError(
                "Gemini model not available. Check your API key at https://aistudio.google.com/apikey"
            )
        raise RuntimeError(f"Gemini API error: {e}")


def chat_with_context(system_prompt: str, messages: list, max_tokens: int = 1024) -> str:
    history_text = ""
    for m in messages[:-1]:
        role = "Owner" if m["role"] == "user" else "Assistant"
        history_text += f"{role}: {m['content']}\n"

    current_msg = messages[-1]["content"] if messages else ""

    full_prompt = (
        f"{system_prompt}\n\n"
        f"--- CONVERSATION HISTORY ---\n{history_text}"
        f"--- CURRENT MESSAGE ---\nOwner: {current_msg}\n\n"
        f"Assistant (respond now):"
    )
    return _call(full_prompt, max_tokens)


def extract_structured_data(text: str) -> dict:
    prompt = (
        "You are a data extraction assistant for a small shop management system.\n"
        "Extract purchase, sale, or expense data from natural language input.\n\n"
        "Return ONLY valid JSON in this exact format (no markdown, no explanation):\n"
        '{\n'
        '  "action": "purchase" | "sale" | "expense" | "query" | "unknown",\n'
        '  "items": [\n'
        '    { "item_name": "string", "quantity": number, "price": number, "unit": "string" }\n'
        '  ],\n'
        '  "expense": { "amount": number, "type": "rent|electricity|salary|supplier|transport|other", "description": "string" },\n'
        '  "raw_query": "string (if action is query)"\n'
        "}\n\n"
        "Rules:\n"
        "- For purchases: price is cost_price per unit\n"
        "- For sales: price is selling_price per unit\n"
        "- If multiple items, list all in items array\n"
        "- If it's a question, set action to 'query'\n"
        "- If unclear, set action to 'unknown'\n"
        "- Only fill relevant fields\n\n"
        f"Input: {text}\n\n"
        "JSON:"
    )

    import json
    try:
        raw = _call(prompt, max_tokens=512)
        # Strip markdown code fences if present
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return {"action": "unknown", "items": [], "raw_query": text}


def generate_offer_message(item_name: str, reason: str, discount_pct: float = None, shop_name: str = "") -> str:
    discount_line = f"Discount: {discount_pct}% off" if discount_pct else ""
    prompt = (
        f"Generate a short, friendly promotional message for a small shop.\n"
        f"Shop: {shop_name}\n"
        f"Product: {item_name}\n"
        f"Reason: {reason}\n"
        f"{discount_line}\n\n"
        "Requirements:\n"
        "- Maximum 3 lines\n"
        "- Friendly and natural tone\n"
        "- No excessive emojis\n"
        "- Sound like a real shop owner, not a corporate ad\n\n"
        "Message:"
    )
    return _call(prompt, max_tokens=150)


def generate_daily_insight(business_data: dict) -> str:
    prompt = (
        "You are a friendly business advisor for a small shop owner.\n"
        "Given today's business data, give a concise, practical insight in 3-4 sentences max.\n"
        "Be specific with numbers. Sound like a knowledgeable friend, not a consultant.\n\n"
        f"Data: {business_data}\n\n"
        "Focus on: what went well, what needs attention, one specific action to take.\n\n"
        "Insight:"
    )
    return _call(prompt, max_tokens=200)


def answer_customer_query(
    query: str,
    inventory_context: str,
    shop_name: str,
    intent_hint: str = "",
) -> str:
    hint_line = f"Note: {intent_hint}\n" if intent_hint else ""
    prompt = (
        f"You are a helpful, friendly assistant for {shop_name}, a small kirana shop.\n"
        "Answer the customer's question concisely (2-3 sentences max).\n"
        "Use the inventory list to give accurate availability and price info.\n"
        "If an item is out of stock, say so and suggest a similar item if available.\n"
        "Reply in the same language/style the customer uses (English or Tanglish is fine).\n"
        f"{hint_line}\n"
        f"Current inventory:\n{inventory_context}\n\n"
        f"Customer: {query}\n\n"
        "Reply:"
    )
    return _call(prompt, max_tokens=160)
