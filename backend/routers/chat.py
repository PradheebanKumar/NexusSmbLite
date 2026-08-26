from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, timedelta
from backend.database import get_db, SessionLocal
from backend import models, auth
from backend.services.claude_service import chat_with_context, extract_structured_data
from backend.agents.finance_agent import FinanceAgent
from backend.agents.inventory_agent import InventoryAgent
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


def build_owner_system_prompt(owner: models.Owner, db: Session) -> str:
    inventory = db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id).all()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_sales = db.query(models.Sale).filter(
        models.Sale.owner_id == owner.id,
        models.Sale.date >= today_start
    ).all()
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == owner.id,
        models.Expense.date >= month_start
    ).all()
    pending_actions = db.query(models.PendingAction).filter(
        models.PendingAction.owner_id == owner.id,
        models.PendingAction.status == "pending"
    ).count()

    inv_summary = "\n".join([
        f"- {i.item_name}: {i.quantity} {i.unit}, cost ₹{i.cost_price}, sell ₹{i.selling_price}"
        for i in inventory[:15]
    ]) or "No inventory yet"

    today_revenue = sum(s.total_amount for s in today_sales)
    month_expense_total = sum(e.amount for e in month_expenses)

    return f"""You are a smart, friendly business advisor for {owner.name}'s shop called "{owner.shop_name}".
You know their business inside out. Talk like a knowledgeable friend — not a corporate advisor.
Be specific with numbers. Be concise. Give actionable advice.

CURRENT BUSINESS DATA:
Shop: {owner.shop_name}
Owner: {owner.name}

Inventory (top 15 items):
{inv_summary}

Today's revenue so far: ₹{today_revenue}
This month's expenses: ₹{month_expense_total}
Pending AI actions waiting for approval: {pending_actions}

CAPABILITIES — when owner says any of these, output ACTION:RECORD|<json> on its own line:
- "bought 50 milk at ₹20"      → ACTION:RECORD|{{"action":"purchase","items":[{{"item_name":"Milk","quantity":50,"price":20,"unit":"units"}}]}}
- "sold 30 milk today"         → ACTION:RECORD|{{"action":"sale","items":[{{"item_name":"Milk","quantity":30}}]}}
- "change milk sell price ₹32" → ACTION:RECORD|{{"action":"price_update","item_name":"Milk","selling_price":32}}
- "milk cost price is ₹22"     → ACTION:RECORD|{{"action":"price_update","item_name":"Milk","cost_price":22}}
- "paid ₹8000 rent"            → ACTION:RECORD|{{"action":"expense","expense":{{"amount":8000,"type":"rent","description":"Monthly rent"}}}}

IMPORTANT: Always output the ACTION line FIRST, then your friendly response.
Never make up data — only record what the owner explicitly states.
Keep responses under 120 words. Be specific with numbers from the data above."""


class ChatMessage(BaseModel):
    message: str


@router.post("/message")
async def send_message(
    req: ChatMessage,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    # Save user message
    user_msg = models.Conversation(owner_id=owner.id, role="user", content=req.message)
    db.add(user_msg)
    db.commit()

    # Get recent conversation history (last 10 messages)
    history = db.query(models.Conversation).filter(
        models.Conversation.owner_id == owner.id
    ).order_by(models.Conversation.created_at.desc()).limit(10).all()
    history.reverse()

    messages = [{"role": m.role, "content": m.content} for m in history]

    system_prompt = build_owner_system_prompt(owner, db)

    # Call Claude
    try:
        response = chat_with_context(system_prompt, messages, max_tokens=512)
    except Exception as e:
        response = f"Sorry, I'm having trouble connecting right now. Error: {str(e)}"

    # Check if response contains an action to record
    action_taken = None
    if "ACTION:RECORD|" in response:
        lines = response.split("\n")
        clean_lines = []
        for line in lines:
            if line.startswith("ACTION:RECORD|"):
                try:
                    json_data = line.replace("ACTION:RECORD|", "").strip()
                    action_data = json.loads(json_data)
                    action_taken = await _process_voice_action(action_data, owner, db)
                except Exception as e:
                    print(f"Action parsing error: {e}")
            else:
                clean_lines.append(line)
        response = "\n".join(clean_lines).strip()

    # Save assistant response
    assistant_msg = models.Conversation(owner_id=owner.id, role="assistant", content=response)
    db.add(assistant_msg)
    db.commit()

    # Append a small confirmation if action was taken successfully
    if action_taken and "error" not in action_taken:
        atype = action_taken.get("type", "")
        if atype == "price_update":
            item = action_taken.get("item", "")
            sp = action_taken.get("selling_price")
            cp = action_taken.get("cost_price")
            parts = []
            if sp: parts.append(f"sell ₹{sp}")
            if cp: parts.append(f"cost ₹{cp}")
            response += f"\n\n✅ *{item} updated: {', '.join(parts)}*"
        elif atype == "purchase":
            response += f"\n\n✅ *Stock updated for {action_taken.get('items_updated', 0)} item(s)*"
        elif atype == "sale":
            response += f"\n\n✅ *Sale recorded for {action_taken.get('items_recorded', 0)} item(s)*"
        elif atype == "expense":
            response += f"\n\n✅ *Expense ₹{action_taken.get('amount')} recorded*"

    return {
        "response": response,
        "action_taken": action_taken,
    }


async def _process_voice_action(data: dict, owner: models.Owner, db: Session) -> dict | None:
    action = data.get("action")
    items = data.get("items", [])
    expense = data.get("expense")

    if action == "purchase" and items:
        for item_data in items:
            inv_item = db.query(models.Inventory).filter(
                models.Inventory.owner_id == owner.id,
                func.lower(models.Inventory.item_name) == item_data.get("item_name", "").lower()
            ).first()
            if inv_item:
                inv_item.quantity += item_data.get("quantity", 0)
                if item_data.get("price"):
                    inv_item.cost_price = item_data["price"]
            else:
                # Create new item with cost price only, selling price = cost * 1.3 as default
                cost = item_data.get("price", 0)
                new_item = models.Inventory(
                    owner_id=owner.id,
                    item_name=item_data.get("item_name", "Unknown"),
                    quantity=item_data.get("quantity", 0),
                    unit=item_data.get("unit", "units"),
                    cost_price=cost,
                    selling_price=round(cost * 1.3, 2),
                )
                db.add(new_item)
        db.commit()
        return {"type": "purchase", "items_updated": len(items)}

    elif action == "sale" and items:
        for item_data in items:
            inv_item = db.query(models.Inventory).filter(
                models.Inventory.owner_id == owner.id,
                func.lower(models.Inventory.item_name) == item_data.get("item_name", "").lower()
            ).first()
            if inv_item:
                qty = item_data.get("quantity", 0)
                sale = models.Sale(
                    owner_id=owner.id,
                    item_name=inv_item.item_name,
                    quantity_sold=qty,
                    selling_price=inv_item.selling_price,
                    total_amount=inv_item.selling_price * qty,
                )
                db.add(sale)
                inv_item.quantity = max(0, inv_item.quantity - qty)
                inv_item.last_sold_date = datetime.utcnow()
        db.commit()
        return {"type": "sale", "items_recorded": len(items)}

    elif action == "price_update":
        item_name = data.get("item_name", "")
        new_sell  = data.get("selling_price")
        new_cost  = data.get("cost_price")
        inv_item  = db.query(models.Inventory).filter(
            models.Inventory.owner_id == owner.id,
            func.lower(models.Inventory.item_name) == item_name.lower()
        ).first()
        if inv_item:
            if new_sell is not None:
                inv_item.selling_price = float(new_sell)
            if new_cost is not None:
                inv_item.cost_price = float(new_cost)
            db.commit()
            return {"type": "price_update", "item": inv_item.item_name,
                    "selling_price": inv_item.selling_price, "cost_price": inv_item.cost_price}
        return {"type": "price_update", "error": f"'{item_name}' not found in inventory"}

    elif action == "expense" and expense:
        exp = models.Expense(
            owner_id=owner.id,
            amount=expense.get("amount", 0),
            expense_type=expense.get("type", "other"),
            description=expense.get("description"),
        )
        db.add(exp)
        db.commit()
        return {"type": "expense", "amount": expense.get("amount")}

    return None


@router.get("/history")
def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    messages = db.query(models.Conversation).filter(
        models.Conversation.owner_id == owner.id
    ).order_by(models.Conversation.created_at.desc()).limit(limit).all()
    messages.reverse()

    return [
        {"role": m.role, "content": m.content, "timestamp": m.created_at}
        for m in messages
    ]


@router.delete("/history")
def clear_history(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    db.query(models.Conversation).filter(models.Conversation.owner_id == owner.id).delete()
    db.commit()
    return {"message": "Chat history cleared"}
