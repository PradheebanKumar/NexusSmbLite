"""
WhatsApp router — Twilio webhook for customer bot.

HOW IT WORKS:
1. Customer sends WhatsApp message to Twilio sandbox number
2. Twilio POSTs the message to this webhook URL
3. Custom ML classifier detects intent (fast, no API cost)
4. Simple intents (GREETING, THANKS, OUT_OF_SCOPE) → instant canned reply
5. Product intents (AVAILABILITY, PRICE, BULK, MULTIPLE) → Gemini with inventory context
6. UNKNOWN intent → Gemini handles it
7. Demand signals logged for unavailable items

WEBHOOK URL FORMAT:
  https://your-domain.com/api/whatsapp/webhook/{owner_id}

Set this in Twilio Console > Messaging > Sandbox Settings > "WHEN A MESSAGE COMES IN"
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend import models, auth
from backend.services.claude_service import answer_customer_query
from backend.services.whatsapp_service import send_whatsapp_message
from backend.ml.classifier import (
    classify_with_confidence, get_canned_reply,
    is_simple_intent, needs_inventory_lookup,
    CONFIDENCE_THRESHOLD, model_is_ready,
)

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


def _twiml_reply(message: str) -> PlainTextResponse:
    """Return a TwiML XML response — this is what Twilio reads to send message back."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""
    return PlainTextResponse(content=xml, media_type="application/xml")


def _build_inventory_context(db: Session, owner_id: int) -> str:
    items = db.query(models.Inventory).filter(models.Inventory.owner_id == owner_id).all()
    if not items:
        return "No items currently in stock."
    lines = []
    for i in items:
        status = "Available" if i.quantity > 0 else "Out of stock"
        lines.append(f"- {i.item_name}: {status}, Price: Rs.{i.selling_price}/{i.unit}, Stock: {i.quantity}")
    return "\n".join(lines)


@router.post("/webhook/{owner_id}")
async def whatsapp_webhook(
    owner_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Twilio sends POST here when a customer messages the WhatsApp number.
    Must return TwiML XML — Twilio reads this to send the reply.
    """
    form_data = await request.form()
    from_number = str(form_data.get("From", ""))
    body = str(form_data.get("Body", "")).strip()

    if not body:
        return _twiml_reply("Hi! How can we help you today?")

    owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()
    if not owner:
        return _twiml_reply("Shop not found. Please contact the shop directly.")

    customer_phone = from_number.replace("whatsapp:", "").strip()

    # ── Step 1: ML Intent Classification ──────────────────────────────────────
    intent, confidence = classify_with_confidence(body)
    use_ml = confidence >= CONFIDENCE_THRESHOLD
    reply = None

    if use_ml and is_simple_intent(intent):
        # Instant canned reply — no DB lookup, no Gemini call
        reply = get_canned_reply(intent)
        if intent == "OUT_OF_SCOPE":
            reply = (
                f"For shop timings, delivery, or other details please call us directly. "
                f"I can help with product availability and prices at {owner.shop_name}!"
            )
    else:
        # ── Step 2: Inventory lookup + Gemini for product questions ──────────
        inventory_context = _build_inventory_context(db, owner_id)

        # Hint to Gemini about what kind of question this is
        intent_hint = ""
        if use_ml:
            labels = {
                "AVAILABILITY_CHECK": "The customer is asking if a product is available.",
                "PRICE_ENQUIRY":      "The customer is asking about the price of a product.",
                "BULK_ORDER":         "The customer wants to order a large quantity.",
                "MULTIPLE_ITEMS":     "The customer is asking about multiple products.",
                "COMPLAINT":          "The customer has a complaint about product quality or service.",
            }
            intent_hint = labels.get(intent, "")

        try:
            reply = answer_customer_query(
                body, inventory_context, owner.shop_name, intent_hint=intent_hint
            )
        except Exception as e:
            reply = f"Thank you for contacting {owner.shop_name}! We'll get back to you shortly."

    # ── Step 3: Log demand signals ────────────────────────────────────────────
    _log_demand_signal(body, db, owner_id, customer_phone, owner_id)

    return _twiml_reply(reply)


def _log_demand_signal(message: str, db: Session, owner_id: int, customer_phone: str, oid: int):
    """Log when customer asks for something not in stock or not available."""
    inventory = db.query(models.Inventory).filter(models.Inventory.owner_id == owner_id).all()
    msg_lower = message.lower()

    # Check each inventory item
    for item in inventory:
        if item.item_name.lower() in msg_lower and item.quantity == 0:
            _upsert_demand(db, owner_id, item.item_name, customer_phone)
            return

    # Check for "not available" patterns — items asked but not in inventory at all
    query_words = {"have", "available", "stock", "sell", "get", "any", "do you"}
    if any(w in msg_lower for w in query_words):
        skip = {"do", "you", "have", "any", "is", "are", "the", "a", "an",
                "i", "want", "need", "looking", "for", "please", "can", "get",
                "available", "stock", "sell", "in", "to", "hi", "hello", "hey"}
        words = [w.strip("?.,!") for w in msg_lower.split() if len(w) > 3 and w not in skip]
        inventory_names = {item.item_name.lower() for item in inventory if item.quantity > 0}
        for word in words[:3]:
            if word not in inventory_names:
                _upsert_demand(db, owner_id, word.title(), customer_phone)


def _upsert_demand(db: Session, owner_id: int, product_name: str, customer_phone: str):
    existing = db.query(models.DemandSignal).filter(
        models.DemandSignal.owner_id == owner_id,
        func.lower(models.DemandSignal.product_name) == product_name.lower()
    ).first()
    if existing:
        existing.count += 1
        from datetime import datetime
        existing.last_requested = datetime.utcnow()
        if customer_phone and customer_phone not in (existing.customer_phone or ""):
            existing.customer_phone = customer_phone
    else:
        signal = models.DemandSignal(
            owner_id=owner_id,
            product_name=product_name,
            count=1,
            customer_phone=customer_phone,
        )
        db.add(signal)
    db.commit()


class CustomerMessage(BaseModel):
    message: str


@router.post("/simulate")
async def simulate_customer_chat(
    req: CustomerMessage,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    """
    In-app customer chat simulator — same AI + inventory logic as WhatsApp bot.
    Also returns intent classification info so you can see what the ML detected.
    """
    # ML classification
    intent, confidence = classify_with_confidence(req.message)
    use_ml = confidence >= CONFIDENCE_THRESHOLD
    reply = None

    if use_ml and is_simple_intent(intent):
        reply = get_canned_reply(intent) or "How can I help you?"
    else:
        inventory_context = _build_inventory_context(db, owner.id)
        labels = {
            "AVAILABILITY_CHECK": "The customer is asking if a product is available.",
            "PRICE_ENQUIRY":      "The customer is asking about the price of a product.",
            "BULK_ORDER":         "The customer wants to order a large quantity.",
            "MULTIPLE_ITEMS":     "The customer is asking about multiple products.",
            "COMPLAINT":          "The customer has a complaint about product quality or service.",
        }
        intent_hint = labels.get(intent, "") if use_ml else ""
        try:
            reply = answer_customer_query(
                req.message, inventory_context, owner.shop_name, intent_hint=intent_hint
            )
        except Exception as e:
            reply = "Sorry, our assistant is busy right now. Please call us directly!"

    _log_demand_signal(req.message, db, owner.id, "in-app-test", owner.id)

    return {
        "reply": reply,
        "shop_name": owner.shop_name,
        "ml_intent": intent,
        "ml_confidence": round(confidence, 3),
        "used_ml": use_ml and is_simple_intent(intent),
        "model_ready": model_is_ready(),
    }


@router.get("/demand-signals")
def get_demand_signals(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    signals = db.query(models.DemandSignal).filter(
        models.DemandSignal.owner_id == owner.id
    ).order_by(models.DemandSignal.count.desc()).all()
    return [
        {
            "product": s.product_name,
            "count": s.count,
            "last_requested": s.last_requested,
            "customer_phone": s.customer_phone,
            "notified": s.notified,
        }
        for s in signals
    ]
