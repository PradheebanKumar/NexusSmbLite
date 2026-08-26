from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from backend.database import get_db
from backend import models, auth
from backend.services.whatsapp_service import send_whatsapp_message

router = APIRouter(prefix="/api/actions", tags=["actions"])


class ActionUpdate(BaseModel):
    status: str  # approved, rejected
    edited_content: Optional[str] = None


@router.get("/")
def get_pending_actions(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    actions = db.query(models.PendingAction).filter(
        models.PendingAction.owner_id == owner.id,
        models.PendingAction.status == "pending"
    ).order_by(models.PendingAction.created_at.desc()).all()

    return [
        {
            "id": a.id,
            "action_type": a.action_type,
            "title": a.title,
            "description": a.description,
            "generated_content": a.generated_content,
            "action_data": a.action_data,
            "status": a.status,
            "created_at": a.created_at,
        }
        for a in actions
    ]


@router.get("/history")
def get_action_history(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    actions = db.query(models.PendingAction).filter(
        models.PendingAction.owner_id == owner.id,
        models.PendingAction.status != "pending"
    ).order_by(models.PendingAction.created_at.desc()).limit(50).all()

    return [
        {
            "id": a.id,
            "action_type": a.action_type,
            "title": a.title,
            "status": a.status,
            "created_at": a.created_at,
            "resolved_at": a.resolved_at,
        }
        for a in actions
    ]


@router.put("/{action_id}")
def resolve_action(
    action_id: int,
    req: ActionUpdate,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    action = db.query(models.PendingAction).filter(
        models.PendingAction.id == action_id,
        models.PendingAction.owner_id == owner.id
    ).first()

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if req.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    if req.edited_content:
        action.generated_content = req.edited_content

    action.status = req.status
    action.resolved_at = datetime.utcnow()

    # Execute approved actions
    if req.status == "approved":
        _execute_action(action, owner, db)

    db.commit()
    return {"message": f"Action {req.status}", "action_id": action_id}


def _execute_action(action: models.PendingAction, owner: models.Owner, db: Session):
    data = action.action_data or {}

    if action.action_type == "send_whatsapp_offer":
        phone = data.get("phone") or owner.whatsapp_number
        if phone and action.generated_content:
            send_whatsapp_message(f"whatsapp:{phone}", action.generated_content)

    elif action.action_type == "update_price":
        item_name = data.get("item_name")
        new_price = data.get("new_price")
        if item_name and new_price:
            from sqlalchemy import func
            item = db.query(models.Inventory).filter(
                models.Inventory.owner_id == owner.id,
                func.lower(models.Inventory.item_name) == item_name.lower()
            ).first()
            if item:
                item.selling_price = new_price

    elif action.action_type == "notify_demand_customers":
        phones = data.get("phones", [])
        message = action.generated_content
        for phone in phones:
            if message:
                send_whatsapp_message(f"whatsapp:{phone}", message)

    action.status = "executed"
