"""
Intent classifier — loads trained model, exposes classify() function.
Lazy-loads the model on first call (no startup cost).

Usage:
    from backend.ml.classifier import classify, classify_with_confidence

    intent = classify("brinjal iruka")
    # → "AVAILABILITY_CHECK"

    intent, confidence = classify_with_confidence("milk price enna")
    # → ("PRICE_ENQUIRY", 0.94)
"""
import os, pickle
from typing import Tuple

MODEL_PATH = os.path.join(os.path.dirname(__file__), "intent_model.pkl")

# Intents that are "simple" — ML can handle alone (no Gemini needed)
SIMPLE_INTENTS = {
    "GREETING",
    "THANKS",
    "OUT_OF_SCOPE",
}

# Intents that need product info from DB — ML detects, Gemini formulates answer
PRODUCT_INTENTS = {
    "AVAILABILITY_CHECK",
    "PRICE_ENQUIRY",
    "BULK_ORDER",
    "MULTIPLE_ITEMS",
}

# Threshold below which we escalate to Gemini
CONFIDENCE_THRESHOLD = 0.55

_pipeline = None


def _load_model():
    global _pipeline
    if _pipeline is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Intent model not found at {MODEL_PATH}. "
                "Run: python -m backend.ml.train"
            )
        with open(MODEL_PATH, "rb") as f:
            _pipeline = pickle.load(f)
    return _pipeline


def classify(text: str) -> str:
    """
    Returns intent string. If model not trained or confidence too low → 'UNKNOWN'.
    """
    intent, confidence = classify_with_confidence(text)
    if confidence < CONFIDENCE_THRESHOLD:
        return "UNKNOWN"
    return intent


def classify_with_confidence(text: str) -> Tuple[str, float]:
    """
    Returns (intent, confidence_score).
    """
    try:
        pipe = _load_model()
        text_clean = text.strip().lower()
        pred = pipe.predict([text_clean])[0]
        proba = pipe.predict_proba([text_clean]).max()
        return pred, float(proba)
    except FileNotFoundError:
        return "UNKNOWN", 0.0
    except Exception as e:
        print(f"[Classifier] Error: {e}")
        return "UNKNOWN", 0.0


def is_simple_intent(intent: str) -> bool:
    """True if the bot can reply without looking up DB / calling Gemini."""
    return intent in SIMPLE_INTENTS


def needs_inventory_lookup(intent: str) -> bool:
    """True if the bot needs to check inventory to answer."""
    return intent in PRODUCT_INTENTS


# Canned replies for simple intents (instant, no API cost)
CANNED_REPLIES = {
    "GREETING": [
        "Vanakkam! Welcome to our shop 🙏 How can I help you today?",
        "Hello! Good to see you. What can I get for you?",
        "Hi there! Ask me about any product — availability, price, or place an order!",
    ],
    "THANKS": [
        "You're welcome! Come again anytime 😊",
        "Happy to help! Have a great day 🙏",
        "Thank you for shopping with us! See you soon.",
    ],
    "OUT_OF_SCOPE": (
        "For shop timings, delivery info, or other queries please call us directly. "
        "I'm best at answering product questions — what would you like to know?"
    ),
}

import random

def get_canned_reply(intent: str) -> str | None:
    """Returns a random canned reply for simple intents, or None."""
    replies = CANNED_REPLIES.get(intent)
    if replies is None:
        return None
    if isinstance(replies, list):
        return random.choice(replies)
    return replies


def model_is_ready() -> bool:
    """Returns True if model file exists and loads correctly."""
    try:
        _load_model()
        return True
    except Exception:
        return False
