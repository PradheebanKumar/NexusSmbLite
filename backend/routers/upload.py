"""
Upload router — handles bill photos and sales file uploads.
Extracts data using Gemini Vision, updates inventory/sales.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from backend.database import get_db
from backend import models, auth
from backend.services.vision_service import (
    extract_bill_from_image,
    extract_sales_from_image,
    extract_sales_from_text,
    suggest_selling_price,
)

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


@router.post("/bill")
async def upload_bill(
    file: UploadFile = File(...),
    apply_immediately: bool = Form(default=False),
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    """
    Upload a purchase bill photo → Gemini extracts items → returns preview.
    If apply_immediately=True, updates inventory straight away.
    Otherwise returns extracted data for owner to review first.
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Upload a JPG, PNG or WebP image of the bill")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    extracted = extract_bill_from_image(image_bytes, file.content_type)

    if "error" in extracted and not extracted.get("items"):
        err_detail = extracted.get("error", "Could not read the bill")
        raise HTTPException(status_code=422, detail=f"Bill read failed: {err_detail}. Try a clearer photo or better lighting.")

    items = extracted.get("items", [])

    if apply_immediately:
        results = _apply_stock_update(items, owner.id, db)
        return {
            "message": f"Stock updated from bill. {len(results['updated'])} items added/updated.",
            "updated": results["updated"],
            "skipped": results["skipped"],
            "bill_date": extracted.get("bill_date"),
            "supplier": extracted.get("supplier_name"),
        }

    # Return preview for owner to confirm/edit
    return {
        "preview": True,
        "bill_date": extracted.get("bill_date"),
        "supplier": extracted.get("supplier_name"),
        "grand_total": extracted.get("grand_total"),
        "items": items,
        "message": "Review extracted items below. Confirm to update inventory."
    }


class BillItem(BaseModel):
    item_name: str
    quantity: float
    unit: str = "units"
    cost_price: float
    suggested_selling_price: Optional[float] = None
    selling_price: Optional[float] = None
    total_amount: Optional[float] = None


@router.post("/bill/confirm")
async def confirm_bill(
    items: List[BillItem],
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    """Apply confirmed/edited bill items to inventory."""
    items_dicts = [i.model_dump() for i in items]
    results = _apply_stock_update(items_dicts, owner.id, db)
    return {
        "message": f"Stock updated. {len(results['updated'])} items added/updated.",
        **results
    }


@router.post("/sales")
async def upload_sales(
    file: Optional[UploadFile] = File(default=None),
    text_data: Optional[str] = Form(default=None),
    sale_date: Optional[str] = Form(default=None),
    apply_immediately: bool = Form(default=False),
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    """
    Upload end-of-day sales as:
    - Image (photo of sales register / notebook)
    - Text (typed or WhatsApp forwarded message)
    Returns preview or applies immediately.
    """
    items = []

    if file and file.content_type in ALLOWED_IMAGE_TYPES:
        image_bytes = await file.read()
        extracted = extract_sales_from_image(image_bytes, file.content_type)
        items = extracted.get("items", [])
    elif text_data:
        extracted = extract_sales_from_text(text_data)
        items = extracted.get("items", [])
    else:
        raise HTTPException(status_code=400, detail="Provide either an image file or text data")

    if not items:
        raise HTTPException(status_code=422, detail="Could not extract any sales data. Try a clearer image or text.")

    target_date = datetime.utcnow()
    if sale_date:
        try:
            target_date = datetime.fromisoformat(sale_date)
        except ValueError:
            target_date = datetime.utcnow() - timedelta(days=1)  # default yesterday

    if apply_immediately:
        results = _apply_sales_update(items, owner.id, target_date, db)
        return {
            "message": f"Sales recorded. {len(results['recorded'])} items updated.",
            **results
        }

    return {
        "preview": True,
        "items": items,
        "message": "Review sales below. Confirm to record."
    }


@router.get("/price-suggestion")
def get_price_suggestion(
    item_name: str,
    cost_price: float,
    owner: models.Owner = Depends(auth.get_current_owner),
):
    """Get auto-suggested selling price for an item."""
    suggestion = suggest_selling_price(item_name, cost_price)
    return suggestion


def _apply_stock_update(items: list, owner_id: int, db: Session) -> dict:
    updated = []
    skipped = []

    for item in items:
        name = item.get("item_name", "").strip()
        qty = item.get("quantity")
        cost = item.get("cost_price")

        if not name or not qty or not cost:
            skipped.append({"item": name, "reason": "missing required fields"})
            continue

        try:
            qty = float(qty)
            cost = float(cost)
        except (TypeError, ValueError):
            skipped.append({"item": name, "reason": "invalid quantity or price"})
            continue

        # Get suggested selling price
        sell_price = item.get("suggested_selling_price") or item.get("selling_price")
        if not sell_price:
            suggestion = suggest_selling_price(name, cost)
            sell_price = suggestion["suggested_price"]

        # Find existing item
        existing = db.query(models.Inventory).filter(
            models.Inventory.owner_id == owner_id,
            func.lower(models.Inventory.item_name) == name.lower()
        ).first()

        if existing:
            existing.quantity += qty
            existing.cost_price = cost
            if sell_price and sell_price > cost:
                existing.selling_price = sell_price
            action = "updated"
        else:
            new_item = models.Inventory(
                owner_id=owner_id,
                item_name=name,
                quantity=qty,
                unit=item.get("unit", "units"),
                cost_price=cost,
                selling_price=sell_price if sell_price and sell_price > cost else round(cost * 1.25, 0),
                low_stock_threshold=10,
            )
            db.add(new_item)
            action = "added"

        updated.append({"item": name, "qty": qty, "cost": cost, "sell": sell_price, "action": action})

    db.commit()
    return {"updated": updated, "skipped": skipped}


def _apply_sales_update(items: list, owner_id: int, sale_date: datetime, db: Session) -> dict:
    recorded = []
    skipped = []

    for item in items:
        name = item.get("item_name", "").strip()
        qty = item.get("quantity_sold")

        if not name or not qty:
            skipped.append({"item": name, "reason": "missing fields"})
            continue

        try:
            qty = float(qty)
        except (TypeError, ValueError):
            skipped.append({"item": name, "reason": "invalid quantity"})
            continue

        inv_item = db.query(models.Inventory).filter(
            models.Inventory.owner_id == owner_id,
            func.lower(models.Inventory.item_name) == name.lower()
        ).first()

        if not inv_item:
            skipped.append({"item": name, "reason": "not in inventory — add stock first"})
            continue

        # Update selling price if provided in sales record
        sell_price = item.get("selling_price")
        if sell_price:
            try:
                inv_item.selling_price = float(sell_price)
            except (TypeError, ValueError):
                pass

        sale = models.Sale(
            owner_id=owner_id,
            item_name=inv_item.item_name,
            quantity_sold=qty,
            selling_price=inv_item.selling_price,
            total_amount=inv_item.selling_price * qty,
            date=sale_date,
        )
        db.add(sale)

        inv_item.quantity = max(0, inv_item.quantity - qty)
        inv_item.last_sold_date = sale_date

        recorded.append({"item": name, "qty": qty, "amount": inv_item.selling_price * qty})

    db.commit()
    return {"recorded": recorded, "skipped": skipped}
