from backend.config import settings


def send_whatsapp_message(to: str, body: str) -> bool:
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print(f"[WhatsApp SIMULATED] To: {to} | Message: {body}")
        return True

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=to if to.startswith("whatsapp:") else f"whatsapp:{to}",
        )
        return message.sid is not None
    except Exception as e:
        print(f"WhatsApp send failed: {e}")
        return False


def send_owner_alert(owner_whatsapp: str, message: str) -> bool:
    if not owner_whatsapp:
        return False
    number = owner_whatsapp if owner_whatsapp.startswith("whatsapp:") else f"whatsapp:{owner_whatsapp}"
    return send_whatsapp_message(number, message)
