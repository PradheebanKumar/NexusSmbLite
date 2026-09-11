"""
Intent Router & Context Grounder — Sessions 1 & 3 of Course Framework.

Session 1 (Understand):
- Goal decomposition (QUERY, ACTION, CLARIFICATION_NEEDED)
- Entity extraction (item_name, price, quantity)
- Constraint validation

Session 3 (Know & Remember):
- Source Authority: Live SQLite query for the extracted entities
- Context Engineering: Feeds exact business records into prompt
"""
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models
from backend.services.claude_service import _call


class IntentRouter:
    def __init__(self, db: Session, owner_id: int):
        self.db = db
        self.owner_id = owner_id

    def decompose(self, user_message: str) -> Dict[str, Any]:
        """
        Deconstructs user input into intent, entities, and detects ambiguity.
        """
        prompt = f"""You are an Intent Decomposition module for a retail business AI.
Analyze the user's message and extract structured intent.

User Message: "{user_message}"

Possible Intents:
- "QUERY_ANALYTICS": Asking for numbers, sales, stock, expenses, profit, or advice.
- "ACTION_UPDATE_PRICE": Wants to change cost or selling price of an item.
- "ACTION_ADJUST_STOCK": Wants to record purchase, arrival, or stock adjustment.
- "ACTION_RECORD_SALE": Wants to record an item sold.
- "ACTION_RECORD_EXPENSE": Wants to log a shop expense (rent, electricity, etc.).
- "PROMOTION": Wants to generate a discount/offer for customers.
- "AMBIGUOUS": The user has an action in mind but omitted critical details (e.g., "change the price" without stating the price, or "order more" without stating the item).
- "GENERAL_CONVERSATION": Greetings, thanks, or general chit-chat.

Respond ONLY with valid JSON in this exact structure:
{{
  "intent": "QUERY_ANALYTICS" | "ACTION_UPDATE_PRICE" | "ACTION_ADJUST_STOCK" | "ACTION_RECORD_SALE" | "ACTION_RECORD_EXPENSE" | "PROMOTION" | "AMBIGUOUS" | "GENERAL_CONVERSATION",
  "confidence": 0.0 to 1.0,
  "entities": {{
    "item_name": "extracted product name or null",
    "quantity": number or null,
    "unit": "units|kg|litres|etc or null",
    "price": number or null,
    "expense_type": "rent|electricity|salary|supplier|other or null",
    "expense_amount": number or null
  }},
  "missing_info": "description of what is missing if AMBIGUOUS, else null",
  "clarification_question": "specific clarifying question to ask the user if AMBIGUOUS, else null"
}}
"""
        try:
            raw = _call(prompt, max_tokens=1024)
            if "```" in raw:
                parts = raw.split("```")
                for p in parts:
                    clean = p.strip().lstrip("json").strip()
                    if clean.startswith("{"):
                        raw = clean
                        break
            parsed = json.loads(raw.strip())
            return parsed
        except Exception as e:
            # Fallback heuristic if LLM call fails
            return {
                "intent": "GENERAL_CONVERSATION",
                "confidence": 0.5,
                "entities": {"item_name": None},
                "missing_info": None,
                "clarification_question": None,
                "error": str(e)
            }

    def ground_context(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Session 3: Source Authority Grounding.
        Queries the SQLite DB for exact records matching the entities.
        """
        grounded = {
            "item_record": None,
            "recent_sales": [],
            "demand_signal": None
        }

        item_name = entities.get("item_name")
        if not item_name:
            return grounded

        # Fetch inventory record
        item = self.db.query(models.Inventory).filter(
            models.Inventory.owner_id == self.owner_id,
            func.lower(models.Inventory.item_name) == item_name.lower().strip()
        ).first()

        if item:
            grounded["item_record"] = {
                "id": item.id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit": item.unit,
                "cost_price": item.cost_price,
                "selling_price": item.selling_price,
                "margin_pct": round(((item.selling_price - item.cost_price) / item.selling_price * 100), 1) if item.selling_price > 0 else 0,
                "low_stock_threshold": item.low_stock_threshold
            }

            # Fetch recent sales for this specific item
            sales = self.db.query(models.Sale).filter(
                models.Sale.owner_id == self.owner_id,
                func.lower(models.Sale.item_name) == item.item_name.lower()
            ).order_by(models.Sale.date.desc()).limit(5).all()

            grounded["recent_sales"] = [
                {"quantity": s.quantity_sold, "amount": s.total_amount, "date": s.date.isoformat() if s.date else None}
                for s in sales
            ]

        # Fetch demand signals if customers asked for this item
        demand = self.db.query(models.DemandSignal).filter(
            models.DemandSignal.owner_id == self.owner_id,
            func.lower(models.DemandSignal.product_name) == item_name.lower().strip()
        ).first()
        if demand:
            grounded["demand_signal"] = {
                "product_name": demand.product_name,
                "request_count": demand.count,
                "last_requested": demand.last_requested.isoformat() if demand.last_requested else None
            }

        return grounded
