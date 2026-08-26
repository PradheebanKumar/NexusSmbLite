from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from backend.database import get_db
from backend import models, auth

router = APIRouter(prefix="/api/sales", tags=["sales"])


class SaleItem(BaseModel):
    item_name: str
    quantity_sold: float


class RecordSalesRequest(BaseModel):
    items: List[SaleItem]
    date: Optional[str] = None  # ISO date string, defaults to today


@router.post("/")
def record_sales(
    req: RecordSalesRequest,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    sale_date = datetime.utcnow()
    if req.date:
        try:
            sale_date = datetime.fromisoformat(req.date)
        except ValueError:
            pass

    results = []
    for item_data in req.items:
        inv_item = db.query(models.Inventory).filter(
            models.Inventory.owner_id == owner.id,
            func.lower(models.Inventory.item_name) == item_data.item_name.lower()
        ).first()

        if not inv_item:
            results.append({"item": item_data.item_name, "status": "not found in inventory"})
            continue

        if inv_item.quantity < item_data.quantity_sold:
            results.append({"item": item_data.item_name, "status": f"insufficient stock ({inv_item.quantity} available)"})
            continue

        total = inv_item.selling_price * item_data.quantity_sold
        sale = models.Sale(
            owner_id=owner.id,
            item_name=inv_item.item_name,
            quantity_sold=item_data.quantity_sold,
            selling_price=inv_item.selling_price,
            total_amount=total,
            date=sale_date,
        )
        db.add(sale)

        # Update inventory
        inv_item.quantity -= item_data.quantity_sold
        inv_item.last_sold_date = sale_date

        results.append({
            "item": inv_item.item_name,
            "quantity": item_data.quantity_sold,
            "amount": total,
            "status": "recorded"
        })

    db.commit()
    return {"results": results}


@router.get("/today")
def get_today_sales(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    sales = db.query(models.Sale).filter(
        models.Sale.owner_id == owner.id,
        models.Sale.date >= today_start
    ).all()

    total_revenue = sum(s.total_amount for s in sales)
    return {
        "sales": [{"item": s.item_name, "quantity": s.quantity_sold, "amount": s.total_amount, "time": s.date} for s in sales],
        "total_revenue": round(total_revenue, 2),
        "total_transactions": len(sales)
    }


@router.get("/summary")
def get_sales_summary(
    days: int = 30,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    since = datetime.utcnow() - timedelta(days=days)
    sales = db.query(models.Sale).filter(
        models.Sale.owner_id == owner.id,
        models.Sale.date >= since
    ).all()

    # Group by item
    item_summary = {}
    for s in sales:
        if s.item_name not in item_summary:
            item_summary[s.item_name] = {"qty": 0, "revenue": 0}
        item_summary[s.item_name]["qty"] += s.quantity_sold
        item_summary[s.item_name]["revenue"] += s.total_amount

    sorted_items = sorted(item_summary.items(), key=lambda x: x[1]["revenue"], reverse=True)

    return {
        "period_days": days,
        "total_revenue": round(sum(s.total_amount for s in sales), 2),
        "total_items_sold": round(sum(s.quantity_sold for s in sales), 2),
        "top_sellers": [{"item": k, **v} for k, v in sorted_items[:5]],
        "all_items": [{"item": k, **v} for k, v in sorted_items],
    }


@router.get("/daily")
def get_daily_sales(
    days: int = 7,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    since = datetime.utcnow() - timedelta(days=days)
    sales = db.query(models.Sale).filter(
        models.Sale.owner_id == owner.id,
        models.Sale.date >= since
    ).all()

    daily = {}
    for s in sales:
        day = s.date.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {"revenue": 0, "transactions": 0}
        daily[day]["revenue"] += s.total_amount
        daily[day]["transactions"] += 1

    return [{"date": k, **v} for k, v in sorted(daily.items())]
