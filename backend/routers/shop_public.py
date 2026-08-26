"""
Public shop router — NO authentication required.
Customers visit /shop/{owner_id} and chat with the bot.

Endpoints:
  GET  /api/shop/{owner_id}/info    → shop name, products list
  POST /api/shop/{owner_id}/chat    → customer sends message, gets reply

Reply strategy (never crashes):
  1. ML classifier detects intent
  2. GREETING/THANKS → instant canned reply
  3. Product question → try Gemini with full inventory context
  4. If Gemini fails → smart DB-based fallback (answers from inventory directly)
  5. OUT_OF_SCOPE → helpful redirect message
"""
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from backend.database import get_db
from backend import models
from backend.services.claude_service import answer_customer_query
from backend.ml.classifier import (
    classify_with_confidence, get_canned_reply,
    is_simple_intent, CONFIDENCE_THRESHOLD,
)

router = APIRouter(prefix="/api/shop", tags=["shop-public"])

INTENT_LABELS = {
    "AVAILABILITY_CHECK": "The customer is asking if a product is available.",
    "PRICE_ENQUIRY":      "The customer is asking about the price of a product.",
    "BULK_ORDER":         "The customer wants to order a large quantity.",
    "MULTIPLE_ITEMS":     "The customer is asking about multiple products.",
    "COMPLAINT":          "The customer has a complaint about product quality or service.",
}


# ── Inventory helpers ──────────────────────────────────────────────────────────

def _get_inventory(db: Session, owner_id: int):
    return db.query(models.Inventory).filter(
        models.Inventory.owner_id == owner_id
    ).order_by(models.Inventory.item_name).all()


def _build_inventory_context(items) -> str:
    if not items:
        return "No items currently in stock."
    available = [i for i in items if i.quantity > 0]
    out_of_stock = [i for i in items if i.quantity == 0]
    lines = []
    if available:
        lines.append("AVAILABLE:")
        for i in available:
            lines.append(f"- {i.item_name}: Rs.{i.selling_price}/{i.unit}, qty {i.quantity}")
    if out_of_stock:
        lines.append("OUT OF STOCK:")
        for i in out_of_stock:
            lines.append(f"- {i.item_name}")
    return "\n".join(lines)


# ── Smart DB-based fallback (works without Gemini) ────────────────────────────

def _find_items_in_message(msg: str, items) -> list:
    """Find inventory items mentioned in the customer's message (fuzzy)."""
    msg_lower = msg.lower()
    found = []
    for item in items:
        name_lower = item.item_name.lower()
        # Direct match
        if name_lower in msg_lower:
            found.append(item)
            continue
        # Partial match: any word of item name appears in message
        for word in name_lower.split():
            if len(word) > 3 and word in msg_lower:
                found.append(item)
                break
    return found


def _db_fallback_reply(msg: str, intent: str, items, shop_name: str) -> str:
    """
    Answer product questions directly from DB without Gemini.
    This ALWAYS returns a useful reply.
    """
    msg_lower = msg.lower()
    found = _find_items_in_message(msg, items)

    # ── AVAILABILITY_CHECK ─────────────────────────────────────────────────────
    if intent in ("AVAILABILITY_CHECK", "UNKNOWN") and not any(
        w in msg_lower for w in ("price", "cost", "rate", "evvalavu", "evlo", "vilai")
    ):
        if not found:
            # List what we have
            in_stock = [i.item_name for i in items if i.quantity > 0]
            if in_stock:
                sample = ", ".join(in_stock[:6])
                return (
                    f"We currently have: {sample}"
                    + (f" and {len(in_stock)-6} more items." if len(in_stock) > 6 else ".")
                    + " Ask me about any specific product!"
                )
            return "We are currently restocking. Please check back soon!"

        replies = []
        for item in found[:3]:
            if item.quantity > 0:
                replies.append(
                    f"{item.item_name} is available at Rs.{item.selling_price}/{item.unit} "
                    f"(qty: {item.quantity})."
                )
            else:
                replies.append(f"Sorry, {item.item_name} is currently out of stock.")
        return " ".join(replies)

    # ── PRICE_ENQUIRY ──────────────────────────────────────────────────────────
    if intent == "PRICE_ENQUIRY" or any(
        w in msg_lower for w in ("price", "cost", "rate", "evvalavu", "evlo", "vilai", "how much", "evlo")
    ):
        if not found:
            return (
                "I couldn't find that product in our stock. "
                "Please ask about a specific item or check our product list!"
            )
        replies = []
        for item in found[:3]:
            if item.quantity > 0:
                replies.append(f"{item.item_name}: Rs.{item.selling_price}/{item.unit}")
            else:
                replies.append(f"{item.item_name} is currently out of stock.")
        return "Price details: " + " | ".join(replies)

    # ── BULK_ORDER ─────────────────────────────────────────────────────────────
    if intent == "BULK_ORDER":
        if found:
            item = found[0]
            if item.quantity > 0:
                return (
                    f"Yes, we have {item.item_name} available (stock: {item.quantity} {item.unit}). "
                    f"Price is Rs.{item.selling_price}/{item.unit}. "
                    "For bulk orders please visit the shop or call us directly!"
                )
            else:
                return f"Sorry, {item.item_name} is out of stock right now. We'll restock soon!"
        return "For bulk orders please visit the shop or call us directly!"

    # ── MULTIPLE_ITEMS ──────────────────────────────────────────────────────────
    if intent == "MULTIPLE_ITEMS":
        if found:
            parts = []
            for item in found[:4]:
                if item.quantity > 0:
                    parts.append(f"{item.item_name} (Rs.{item.selling_price}/{item.unit}) [available]")
                else:
                    parts.append(f"{item.item_name} [out of stock]")
            return "Here's what we have:\n" + "\n".join(parts)
        return "Please ask about specific products and I'll check for you!"

    # ── COMPLAINT ───────────────────────────────────────────────────────────────
    if intent == "COMPLAINT":
        return (
            "We're sorry to hear that! Your feedback matters to us. "
            f"Please visit {shop_name} directly or call us so we can make it right."
        )

    # ── Generic fallback ───────────────────────────────────────────────────────
    if found:
        item = found[0]
        if item.quantity > 0:
            return f"{item.item_name} is available at Rs.{item.selling_price}/{item.unit}."
        return f"Sorry, {item.item_name} is currently out of stock."

    in_stock = [i.item_name for i in items if i.quantity > 0]
    if in_stock:
        sample = ", ".join(in_stock[:5])
        return f"We have: {sample}. Ask me about any product for price or availability!"
    return "Please visit the shop or call us for the latest stock information!"


# ── Demand signal logging ──────────────────────────────────────────────────────

def _log_demand(message: str, intent: str, db: Session, owner_id: int, customer_name: str, items):
    """Log demand for product-related queries only."""
    if intent not in ("AVAILABILITY_CHECK", "PRICE_ENQUIRY", "BULK_ORDER", "MULTIPLE_ITEMS", "UNKNOWN"):
        return

    # Match known inventory items
    found = _find_items_in_message(message, items)
    logged = False
    for item in found:
        _upsert_demand(db, owner_id, item.item_name, customer_name)
        logged = True

    # If no match, extract keywords as unknown product demand
    if not logged and intent != "UNKNOWN":
        skip = {
            "do", "you", "have", "any", "is", "are", "the", "a", "an",
            "i", "want", "need", "please", "can", "get", "available",
            "stock", "sell", "in", "to", "hi", "hello", "hey", "what",
            "price", "cost", "rate", "much", "how", "and", "or", "for",
            "iruka", "irukkuma", "kittaya", "kidaikuma", "vennum", "enna",
            "evvalavu", "evlo", "sir", "anna", "bro", "there",
        }
        words = [
            w.strip("?.,!") for w in message.lower().split()
            if len(w) > 3 and w.strip("?.,!") not in skip
        ]
        for word in words[:2]:
            _upsert_demand(db, owner_id, word.title(), customer_name)


def _upsert_demand(db: Session, owner_id: int, product_name: str, customer_name: str):
    existing = db.query(models.DemandSignal).filter(
        models.DemandSignal.owner_id == owner_id,
        func.lower(models.DemandSignal.product_name) == product_name.lower()
    ).first()
    if existing:
        existing.count += 1
        existing.last_requested = datetime.utcnow()
        if customer_name and customer_name not in (existing.customer_phone or ""):
            existing.customer_phone = customer_name
    else:
        db.add(models.DemandSignal(
            owner_id=owner_id,
            product_name=product_name,
            count=1,
            customer_phone=customer_name,
        ))
    db.commit()


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/{owner_id}/deals")
def get_shop_deals(owner_id: int, db: Session = Depends(get_db)):
    """
    Returns items currently on discount/offer.
    Source: PendingActions with type='discount' that are pending or approved,
    cross-referenced with live inventory to confirm item is in stock.
    Owner applies a discount via Revenue Advisor → appears here automatically.
    """
    owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Get all discount actions (pending or approved = active deal)
    discount_actions = db.query(models.PendingAction).filter(
        models.PendingAction.owner_id == owner_id,
        models.PendingAction.action_type == "discount",
        models.PendingAction.status.in_(["pending", "approved"]),
    ).order_by(models.PendingAction.created_at.desc()).all()

    # Build inventory lookup for quick access
    inv_items = db.query(models.Inventory).filter(
        models.Inventory.owner_id == owner_id,
        models.Inventory.quantity > 0,
    ).all()
    inv_map = {i.item_name.lower(): i for i in inv_items}

    deals = []
    seen = set()  # avoid duplicates
    for action in discount_actions:
        ad = action.action_data or {}
        item_name = ad.get("item_name", "")
        suggested_price = ad.get("suggested_price", 0)
        original_price = ad.get("current_price", 0)

        if not item_name or item_name.lower() in seen:
            continue

        inv = inv_map.get(item_name.lower())
        if not inv or not suggested_price:
            continue

        # Only show as a deal if the discount price is actually lower than current price
        deal_price = min(suggested_price, inv.selling_price)
        og_price = original_price if original_price > deal_price else inv.selling_price

        if deal_price < og_price:
            seen.add(item_name.lower())
            pct_off = round((og_price - deal_price) / og_price * 100)
            deals.append({
                "name": inv.item_name,
                "original_price": round(og_price, 2),
                "deal_price": round(deal_price, 2),
                "unit": inv.unit,
                "stock": inv.quantity,
                "pct_off": pct_off,
            })

    return {"shop_name": owner.shop_name, "deals": deals}


@router.get("/{owner_id}/info")
def get_shop_info(owner_id: int, db: Session = Depends(get_db)):
    owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Shop not found")

    items = db.query(models.Inventory).filter(
        models.Inventory.owner_id == owner_id,
        models.Inventory.quantity > 0,
    ).order_by(models.Inventory.item_name).all()

    return {
        "owner_id": owner_id,
        "shop_name": owner.shop_name,
        "owner_name": owner.name,
        "products": [
            {"name": i.item_name, "price": i.selling_price, "unit": i.unit}
            for i in items
        ],
    }


class ChatRequest(BaseModel):
    message: str
    customer_name: str = "Customer"


def _get_active_deals(db: Session, owner_id: int) -> list:
    """Return active discount deals for this shop (same logic as /deals endpoint)."""
    discount_actions = db.query(models.PendingAction).filter(
        models.PendingAction.owner_id == owner_id,
        models.PendingAction.action_type == "discount",
        models.PendingAction.status.in_(["pending", "approved"]),
    ).all()

    inv_items = db.query(models.Inventory).filter(
        models.Inventory.owner_id == owner_id,
        models.Inventory.quantity > 0,
    ).all()
    inv_map = {i.item_name.lower(): i for i in inv_items}

    deals, seen = [], set()
    for action in discount_actions:
        ad = action.action_data or {}
        item_name = ad.get("item_name", "")
        suggested_price = ad.get("suggested_price", 0)
        original_price = ad.get("current_price", 0)
        if not item_name or item_name.lower() in seen:
            continue
        inv = inv_map.get(item_name.lower())
        if not inv or not suggested_price:
            continue
        deal_price = min(suggested_price, inv.selling_price)
        og_price = original_price if original_price > deal_price else inv.selling_price
        if deal_price < og_price:
            seen.add(item_name.lower())
            deals.append({
                "name": inv.item_name, "unit": inv.unit,
                "deal_price": round(deal_price, 2), "original_price": round(og_price, 2),
                "pct_off": round((og_price - deal_price) / og_price * 100),
            })
    return deals


@router.post("/{owner_id}/chat")
async def customer_chat(
    owner_id: int,
    req: ChatRequest,
    db: Session = Depends(get_db),
):
    owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Shop not found")

    msg = req.message.strip()
    if not msg:
        return {"reply": f"Hi! Welcome to {owner.shop_name}. How can I help you?"}

    # Load inventory once — used for context, fallback, and demand logging
    items = _get_inventory(db, owner_id)

    # Check if customer is asking about deals/offers
    deal_keywords = ["deal", "offer", "discount", "sale", "cheap", "special", "today's", "offer"]
    if any(k in msg.lower() for k in deal_keywords):
        active_deals = _get_active_deals(db, owner_id)
        if active_deals:
            deal_lines = [
                f"- {d['name']}: Rs.{d['deal_price']}/{d['unit']} (was Rs.{d['original_price']}, {d['pct_off']}% off)"
                for d in active_deals
            ]
            reply = f"Today's special offers at {owner.shop_name}:\n" + "\n".join(deal_lines) + "\n\nAsk me about any of these for more details!"
            _log_demand(msg, "PRICE_ENQUIRY", db, owner_id, req.customer_name, items)
            return {
                "reply": reply,
                "shop_name": owner.shop_name,
                "ml_intent": "PRICE_ENQUIRY",
                "ml_confidence": 1.0,
                "used_ml_reply": True,
            }
        else:
            reply = f"No special offers right now at {owner.shop_name}. Ask me about any product for the current price!"
            return {"reply": reply, "shop_name": owner.shop_name, "ml_intent": "PRICE_ENQUIRY", "ml_confidence": 1.0, "used_ml_reply": True}

    # Step 1: ML intent classification
    intent, confidence = classify_with_confidence(msg)
    use_ml = confidence >= CONFIDENCE_THRESHOLD

    reply = None

    # Step 2: Simple intents → instant canned reply (no DB/AI needed)
    if use_ml and is_simple_intent(intent):
        if intent == "OUT_OF_SCOPE":
            reply = (
                f"For delivery, timings, or other details please contact {owner.shop_name} directly. "
                "I can help you with product availability and prices!"
            )
        else:
            reply = get_canned_reply(intent)

    # Step 3: Product questions → try Gemini first, fall back to DB
    else:
        inventory_context = _build_inventory_context(items)
        intent_hint = INTENT_LABELS.get(intent, "") if use_ml else ""

        gemini_ok = False
        try:
            reply = answer_customer_query(
                msg, inventory_context, owner.shop_name, intent_hint=intent_hint
            )
            gemini_ok = True
        except Exception as e:
            # Log the real error for debugging but don't crash
            print(f"[CustomerBot] Gemini failed ({type(e).__name__}: {e}), using DB fallback")

        # Step 4: DB fallback — always gives a useful answer
        if not gemini_ok or not reply:
            reply = _db_fallback_reply(msg, intent, items, owner.shop_name)

    # Step 5: Log demand signal
    _log_demand(msg, intent, db, owner_id, req.customer_name, items)

    return {
        "reply": reply,
        "shop_name": owner.shop_name,
        "ml_intent": intent,
        "ml_confidence": round(confidence, 3),
        "used_ml_reply": use_ml and is_simple_intent(intent),
    }
