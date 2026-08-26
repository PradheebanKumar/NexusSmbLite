from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from backend.database import get_db
from backend import models, auth

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


class InventoryCreate(BaseModel):
    item_name: str
    quantity: float
    unit: str = "units"
    cost_price: float
    selling_price: float
    low_stock_threshold: float = 10


class InventoryUpdate(BaseModel):
    item_name: Optional[str] = None
    quantity: Optional[float] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    low_stock_threshold: Optional[float] = None
    unit: Optional[str] = None


class AddStockRequest(BaseModel):
    item_name: str
    quantity: float
    cost_price: Optional[float] = None


@router.get("/")
def get_inventory(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    items = db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id).all()
    result = []
    today = datetime.utcnow()
    for item in items:
        days_since_sold = None
        if item.last_sold_date:
            days_since_sold = (today - item.last_sold_date.replace(tzinfo=None)).days
        profit = item.selling_price - item.cost_price
        margin_pct = (profit / item.selling_price * 100) if item.selling_price > 0 else 0
        result.append({
            "id": item.id,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "cost_price": item.cost_price,
            "selling_price": item.selling_price,
            "low_stock_threshold": item.low_stock_threshold,
            "last_sold_date": item.last_sold_date,
            "profit_per_unit": round(profit, 2),
            "margin_pct": round(margin_pct, 1),
            "days_since_sold": days_since_sold,
            "is_dead_stock": days_since_sold is not None and days_since_sold > 14,
            "is_slow_mover": days_since_sold is not None and days_since_sold > 7,
            "is_low_stock": item.quantity <= item.low_stock_threshold,
        })
    return result


@router.post("/")
def add_item(
    req: InventoryCreate,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    # Check if item already exists (case-insensitive)
    existing = db.query(models.Inventory).filter(
        models.Inventory.owner_id == owner.id,
        func.lower(models.Inventory.item_name) == req.item_name.lower()
    ).first()

    if existing:
        existing.quantity += req.quantity
        existing.cost_price = req.cost_price
        existing.selling_price = req.selling_price
        db.commit()
        return {"message": f"Updated existing item '{existing.item_name}'", "id": existing.id}

    item = models.Inventory(
        owner_id=owner.id,
        item_name=req.item_name,
        quantity=req.quantity,
        unit=req.unit,
        cost_price=req.cost_price,
        selling_price=req.selling_price,
        low_stock_threshold=req.low_stock_threshold,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": f"Added '{item.item_name}' to inventory", "id": item.id}


@router.post("/add-stock")
def add_stock(
    req: AddStockRequest,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    item = db.query(models.Inventory).filter(
        models.Inventory.owner_id == owner.id,
        func.lower(models.Inventory.item_name) == req.item_name.lower()
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{req.item_name}' not found in inventory")

    item.quantity += req.quantity
    if req.cost_price:
        item.cost_price = req.cost_price
    db.commit()
    return {"message": f"Added {req.quantity} {item.unit} of {item.item_name}", "new_quantity": item.quantity}


@router.put("/{item_id}")
def update_item(
    item_id: int,
    req: InventoryUpdate,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    item = db.query(models.Inventory).filter(
        models.Inventory.id == item_id,
        models.Inventory.owner_id == owner.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if req.item_name is not None:
        item.item_name = req.item_name
    if req.quantity is not None:
        item.quantity = req.quantity
    if req.cost_price is not None:
        item.cost_price = req.cost_price
    if req.selling_price is not None:
        item.selling_price = req.selling_price
    if req.low_stock_threshold is not None:
        item.low_stock_threshold = req.low_stock_threshold
    if req.unit is not None:
        item.unit = req.unit

    db.commit()
    return {"message": "Item updated"}


@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    item = db.query(models.Inventory).filter(
        models.Inventory.id == item_id,
        models.Inventory.owner_id == owner.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item deleted"}


@router.get("/alerts")
def get_inventory_alerts(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    items = db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id).all()
    alerts = []
    today = datetime.utcnow()

    for item in items:
        if item.quantity <= item.low_stock_threshold:
            alerts.append({
                "type": "low_stock",
                "item": item.item_name,
                "message": f"{item.item_name} is low ({item.quantity} {item.unit} left). Reorder soon.",
                "severity": "high"
            })
        if item.last_sold_date:
            days = (today - item.last_sold_date.replace(tzinfo=None)).days
            if days > 14:
                alerts.append({
                    "type": "dead_stock",
                    "item": item.item_name,
                    "message": f"{item.item_name} hasn't sold in {days} days. Consider a discount.",
                    "severity": "medium"
                })
            elif days > 7:
                alerts.append({
                    "type": "slow_mover",
                    "item": item.item_name,
                    "message": f"{item.item_name} is moving slowly ({days} days since last sale).",
                    "severity": "low"
                })
    return alerts
