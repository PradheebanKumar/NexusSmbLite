"""
Vision Service — uses Gemini 2.0 Flash multimodal to extract data from
bill photos, sales register photos, and handwritten notes.
"""
import google.generativeai as genai
import json
import io
from PIL import Image
from backend.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = genai.GenerativeModel("gemini-2.5-flash")

# Common packaged goods MRP database (India)
COMMON_MRP_DB = {
    "parle-g 100g": 5, "parle g 100g": 5, "parle-g": 5, "parle g": 5,
    "parle-g 50g": 5, "parle g biscuit": 5, "parle biscuit": 5,
    "britannia marie 200g": 30, "marie biscuit": 30, "marie gold": 30,
    "good day 100g": 20, "bourbon 100g": 20, "hide and seek": 30,
    "colgate 100g": 55, "colgate 200g": 100, "colgate toothpaste": 55,
    "pepsodent 100g": 50, "pepsodent toothpaste": 50,
    "surf excel 500g": 100, "surf excel 1kg": 190, "surf excel": 100,
    "ariel 500g": 110, "tide 500g": 50,
    "vim bar": 10, "vim liquid 500ml": 90,
    "amul butter 100g": 58, "amul butter 500g": 270, "amul butter": 58,
    "amul milk 500ml": 25, "amul taaza 500ml": 25, "amul milk": 25,
    "aavin milk 500ml": 25, "aavin curd 200g": 22, "aavin curd": 22,
    "horlicks 200g": 135, "bournvita 200g": 130, "boost 200g": 130,
    "nescafe 50g": 120, "bru 50g": 95,
    "tata salt 1kg": 24, "tata salt": 24, "iodised salt": 20,
    "fortune sunflower oil 1l": 135, "sunflower oil 1l": 135,
    "aashirvaad atta 1kg": 55, "atta 1kg": 55, "wheat flour 1kg": 45,
    "maggi 70g": 14, "maggi noodles": 14, "maggi": 14,
    "lays 26g": 20, "kurkure 22g": 10, "bingo 22g": 20,
    "coca cola 600ml": 40, "pepsi 600ml": 38, "sprite 600ml": 38,
    "frooti 200ml": 15, "maaza 200ml": 15, "slice 200ml": 15,
    "dettol soap 75g": 35, "lux soap 75g": 30, "lifebuoy soap": 25,
    "dove soap 75g": 48, "hamam soap 75g": 25,
    "head shoulders 180ml": 180, "dove shampoo 180ml": 200,
    "lifebuoy handwash 200ml": 60, "dettol handwash 200ml": 75,
    "clinic plus 80ml": 60, "sunsilk 80ml": 60,
    "parachute coconut oil 100ml": 55, "parachute 200ml": 95,
    "red label tea 250g": 110, "tata tea gold 250g": 120,
    "brooke bond 250g": 110,
    "mtr sambar powder 100g": 35, "mtr rasam powder": 30,
    "aachi sambar powder": 35, "aachi rasam powder": 30,
}

# Standard margin by category for loose goods
CATEGORY_MARGINS = {
    "rice": 0.30, "boiled rice": 0.30, "raw rice": 0.28,
    "dal": 0.22, "toor": 0.22, "moong": 0.22, "chana": 0.22,
    "oil": 0.22, "sunflower": 0.22, "gingelly": 0.25,
    "flour": 0.20, "maida": 0.20, "atta": 0.20,
    "sugar": 0.12, "jaggery": 0.20,
    "salt": 0.15,
    "vegetables": 0.35, "onion": 0.35, "tomato": 0.35, "potato": 0.30,
    "fruits": 0.35, "banana": 0.30, "apple": 0.35,
    "milk": 0.25, "curd": 0.22,
    "bread": 0.27,
    "eggs": 0.30, "egg": 0.30,
    "spices": 0.30, "pepper": 0.30, "turmeric": 0.30,
    "coconut": 0.25,
    "default": 0.25,
}


def suggest_selling_price(item_name: str, cost_price: float) -> dict:
    name_lower = item_name.lower().strip()

    # Check MRP DB
    for key, mrp in COMMON_MRP_DB.items():
        if key in name_lower or name_lower in key:
            margin = ((mrp - cost_price) / mrp * 100) if mrp > 0 else 0
            return {
                "suggested_price": float(mrp),
                "source": "mrp_database",
                "reasoning": f"Standard MRP for {item_name} is Rs.{mrp}",
                "margin_pct": round(margin, 1),
            }

    # Detect category
    margin = CATEGORY_MARGINS["default"]
    category = "default"
    for cat, cat_margin in CATEGORY_MARGINS.items():
        if cat in name_lower:
            margin = cat_margin
            category = cat
            break

    suggested = cost_price * (1 + margin)
    # Round to nearest 5 for clean pricing
    suggested = round(suggested / 5) * 5
    if suggested <= cost_price:
        suggested = cost_price + 5

    return {
        "suggested_price": float(suggested),
        "source": "margin_rule",
        "reasoning": f"Standard {int(margin*100)}% margin for {category} items",
        "margin_pct": round((suggested - cost_price) / suggested * 100, 1),
    }


def _open_image(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes))


def extract_bill_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Extract purchase/stock data from a bill photo using Gemini Vision."""
    try:
        pil_image = _open_image(image_bytes)
    except Exception as e:
        return {"error": f"Cannot open image: {e}", "items": []}

    prompt = """You are extracting purchase bill data for a small shop inventory system in India.

Look at this bill/invoice image carefully and extract ALL items.

Return ONLY valid JSON (no markdown, no explanation):
{
  "bill_date": "YYYY-MM-DD or null",
  "supplier_name": "string or null",
  "items": [
    {
      "item_name": "string",
      "quantity": number,
      "unit": "units or kg or g or litre or ml or pack or box or dozen or piece",
      "cost_price": number,
      "total_amount": number
    }
  ],
  "grand_total": number or null
}

Rules:
- item_name: clean short name (e.g. "Milk 500ml", "Toor Dal", "Rice")
- quantity: numeric count only
- unit: standardize (pkt->pack, ltr->litre, nos->units, kgs->kg)
- cost_price: price PER UNIT (divide total by qty if needed)
- If image is unclear in parts, extract what you can clearly see
- Return at least an empty items array, never return non-JSON"""

    try:
        response = _model.generate_content(
            [prompt, pil_image],
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1500,
                temperature=0.1,
            ),
        )
        raw = response.text.strip()
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            return {"error": "Gemini API quota exceeded — get a new free key at https://aistudio.google.com/apikey and update GEMINI_API_KEY in your .env file", "items": []}
        if "404" in err or "not found" in err.lower():
            return {"error": "Gemini model not available for your API key", "items": []}
        return {"error": f"Gemini API error: {e}", "items": []}

    # Clean up response
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    try:
        data = json.loads(raw.strip())
        # Add selling price suggestions
        for item in data.get("items", []):
            cost = item.get("cost_price", 0)
            if cost and cost > 0:
                suggestion = suggest_selling_price(item["item_name"], float(cost))
                item["suggested_selling_price"] = suggestion["suggested_price"]
                item["price_reasoning"] = suggestion["reasoning"]
        return data
    except json.JSONDecodeError:
        # Try to extract partial JSON
        return {"error": "Could not parse response", "raw_response": raw[:500], "items": []}


def extract_sales_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Extract end-of-day sales from handwritten register or printed report photo."""
    try:
        pil_image = _open_image(image_bytes)
    except Exception as e:
        return {"error": f"Cannot open image: {e}", "items": []}

    prompt = """You are extracting daily sales data for a small shop in India.

Look at this image (handwritten sales register, notebook, receipt, or printed list).
Extract ALL items sold with quantities.

Return ONLY valid JSON:
{
  "date": "YYYY-MM-DD or null",
  "items": [
    {
      "item_name": "string",
      "quantity_sold": number,
      "unit": "units or kg or g or litre or pack or piece",
      "selling_price": number or null
    }
  ],
  "total_revenue": number or null
}

Rules:
- Extract every readable item
- quantity_sold: how many were sold
- selling_price: per unit price if mentioned
- Make best guess for unclear text based on common shop items
- Always return valid JSON with at least an empty items array"""

    try:
        response = _model.generate_content(
            [prompt, pil_image],
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1500,
                temperature=0.1,
            ),
        )
        raw = response.text.strip()
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            return {"error": "Gemini API quota exceeded — get a new free key at https://aistudio.google.com/apikey", "items": []}
        return {"error": f"Gemini API error: {e}", "items": []}

    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {"error": "Could not parse", "items": []}


def extract_sales_from_text(text: str) -> dict:
    """Extract sales from typed/WhatsApp text message."""
    prompt = f"""Extract daily sales data from this message sent by a shop owner in India.

Message: "{text}"

Return ONLY valid JSON:
{{
  "items": [
    {{
      "item_name": "string",
      "quantity_sold": number,
      "unit": "units or kg or g or litre or pack or piece",
      "selling_price": number or null
    }}
  ]
}}

Extract every item and quantity mentioned. Common patterns:
- "sold 35 milk" -> item_name: "Milk", quantity_sold: 35
- "18 bread packets" -> item_name: "Bread", quantity_sold: 18
- "8kg rice" -> item_name: "Rice", quantity_sold: 8, unit: "kg"
- "milk 35, bread 18, rice 8kg" -> extract all 3"""

    try:
        response = _model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=512,
                temperature=0.1,
            ),
        )
        raw = response.text.strip()
    except Exception as e:
        return {"items": []}

    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {"items": []}
