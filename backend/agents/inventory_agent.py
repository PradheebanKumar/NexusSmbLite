from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models


class InventoryAgent:
    def __init__(self, db: Session, owner_id: int):
        self.db = db
        self.owner_id = owner_id

    def get_all_items(self):
        return self.db.query(models.Inventory).filter(
            models.Inventory.owner_id == self.owner_id
        ).all()

    def detect_low_stock(self) -> list:
        items = self.get_all_items()
        return [
            {
                "item": i.item_name,
                "quantity": i.quantity,
                "unit": i.unit,
                "threshold": i.low_stock_threshold,
                "message": f"{i.item_name} is running low — only {i.quantity} {i.unit} left."
            }
            for i in items if i.quantity <= i.low_stock_threshold
        ]

    def detect_slow_movers(self, days_threshold: int = 7) -> list:
        items = self.get_all_items()
        slow = []
        today = datetime.utcnow()
        for item in items:
            if item.last_sold_date is None:
                continue
            days = (today - item.last_sold_date.replace(tzinfo=None)).days
            if days >= days_threshold:
                slow.append({
                    "item": item.item_name,
                    "days_since_sold": days,
                    "quantity_in_stock": item.quantity,
                    "potential_loss": round(item.cost_price * item.quantity, 2),
                    "message": f"{item.item_name} hasn't sold in {days} days. {item.quantity} {item.unit} in stock."
                })
        return sorted(slow, key=lambda x: x["days_since_sold"], reverse=True)

    def detect_dead_stock(self) -> list:
        return self.detect_slow_movers(days_threshold=14)

    def get_sales_velocity(self, item_name: str, days: int = 14) -> float:
        since = datetime.utcnow() - timedelta(days=days)
        total = self.db.query(func.sum(models.Sale.quantity_sold)).filter(
            models.Sale.owner_id == self.owner_id,
            func.lower(models.Sale.item_name) == item_name.lower(),
            models.Sale.date >= since
        ).scalar()
        return round((total or 0) / days, 2)

    def estimate_days_until_stockout(self, item_name: str) -> dict | None:
        item = self.db.query(models.Inventory).filter(
            models.Inventory.owner_id == self.owner_id,
            func.lower(models.Inventory.item_name) == item_name.lower()
        ).first()
        if not item:
            return None

        velocity = self.get_sales_velocity(item.item_name)
        if velocity <= 0:
            return {"item": item.item_name, "days_until_stockout": None, "message": "No recent sales data"}

        days_left = item.quantity / velocity
        return {
            "item": item.item_name,
            "current_stock": item.quantity,
            "daily_velocity": velocity,
            "days_until_stockout": round(days_left, 1),
            "message": f"{item.item_name} will run out in ~{round(days_left)} days at current sales rate."
        }

    def check_demand_signals(self, threshold: int = 3) -> list:
        signals = self.db.query(models.DemandSignal).filter(
            models.DemandSignal.owner_id == self.owner_id,
            models.DemandSignal.count >= threshold,
            models.DemandSignal.notified == False
        ).all()

        result = []
        for s in signals:
            # Check if item is in inventory
            in_stock = self.db.query(models.Inventory).filter(
                models.Inventory.owner_id == self.owner_id,
                func.lower(models.Inventory.item_name) == s.product_name.lower()
            ).first()

            result.append({
                "product": s.product_name,
                "demand_count": s.count,
                "in_stock": in_stock is not None,
                "message": f"{s.product_name} requested {s.count} times but {'low stock' if in_stock else 'not in inventory'}."
            })
        return result

    def run_full_check(self) -> dict:
        return {
            "low_stock": self.detect_low_stock(),
            "slow_movers": self.detect_slow_movers(),
            "dead_stock": self.detect_dead_stock(),
            "demand_signals": self.check_demand_signals(),
        }
