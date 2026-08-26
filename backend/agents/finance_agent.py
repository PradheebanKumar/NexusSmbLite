from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models


class FinanceAgent:
    def __init__(self, db: Session, owner_id: int):
        self.db = db
        self.owner_id = owner_id

    def profit_per_unit(self, cost: float, sell: float) -> float:
        return round(sell - cost, 2)

    def break_even_units(self, fixed_costs: float, profit_per_unit: float) -> float:
        if profit_per_unit <= 0:
            return float("inf")
        return round(fixed_costs / profit_per_unit, 1)

    def revenue_projection(self, sell_price: float, units: float) -> float:
        return round(sell_price * units, 2)

    def get_monthly_expenses(self) -> float:
        since = datetime.utcnow() - timedelta(days=30)
        total = self.db.query(func.sum(models.Expense.amount)).filter(
            models.Expense.owner_id == self.owner_id,
            models.Expense.date >= since
        ).scalar()
        return round(total or 0, 2)

    def get_today_summary(self) -> dict:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        sales = self.db.query(models.Sale).filter(
            models.Sale.owner_id == self.owner_id,
            models.Sale.date >= today_start
        ).all()

        inventory_map = {
            i.item_name.lower(): i.cost_price
            for i in self.db.query(models.Inventory).filter(
                models.Inventory.owner_id == self.owner_id
            ).all()
        }

        revenue = sum(s.total_amount for s in sales)
        cogs = sum(inventory_map.get(s.item_name.lower(), 0) * s.quantity_sold for s in sales)
        gross_profit = revenue - cogs

        return {
            "revenue": round(revenue, 2),
            "cogs": round(cogs, 2),
            "gross_profit": round(gross_profit, 2),
            "transactions": len(sales),
        }

    def get_cash_flow_warning(self) -> dict | None:
        monthly_expenses = self.get_monthly_expenses()
        since = datetime.utcnow() - timedelta(days=7)
        recent_sales = self.db.query(models.Sale).filter(
            models.Sale.owner_id == self.owner_id,
            models.Sale.date >= since
        ).all()

        weekly_revenue = sum(s.total_amount for s in recent_sales)
        daily_avg = weekly_revenue / 7
        days_left_in_month = 30 - datetime.utcnow().day
        projected_remaining = daily_avg * days_left_in_month

        # Get expenses paid so far this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        paid_so_far = self.db.query(func.sum(models.Expense.amount)).filter(
            models.Expense.owner_id == self.owner_id,
            models.Expense.date >= month_start
        ).scalar() or 0

        remaining_expenses = monthly_expenses - paid_so_far
        if projected_remaining < remaining_expenses and remaining_expenses > 0:
            shortfall = remaining_expenses - projected_remaining
            return {
                "warning": True,
                "shortfall": round(shortfall, 2),
                "projected_revenue": round(projected_remaining, 2),
                "remaining_expenses": round(remaining_expenses, 2),
                "message": f"Cash warning: At current sales rate, you may be short by ₹{round(shortfall, 2)} for upcoming expenses."
            }
        return None

    def analyze_item_economics(self, item_name: str) -> dict:
        item = self.db.query(models.Inventory).filter(
            models.Inventory.owner_id == self.owner_id,
            func.lower(models.Inventory.item_name) == item_name.lower()
        ).first()

        if not item:
            return {"error": "Item not found"}

        monthly_expenses = self.get_monthly_expenses()
        profit = self.profit_per_unit(item.cost_price, item.selling_price)
        bep = self.break_even_units(monthly_expenses, profit)
        margin_pct = (profit / item.selling_price * 100) if item.selling_price > 0 else 0

        since = datetime.utcnow() - timedelta(days=30)
        sold = self.db.query(func.sum(models.Sale.quantity_sold)).filter(
            models.Sale.owner_id == self.owner_id,
            func.lower(models.Sale.item_name) == item_name.lower(),
            models.Sale.date >= since
        ).scalar() or 0

        return {
            "item": item.item_name,
            "cost_price": item.cost_price,
            "selling_price": item.selling_price,
            "profit_per_unit": profit,
            "margin_pct": round(margin_pct, 1),
            "break_even_units": bep,
            "sold_this_month": round(sold, 1),
            "monthly_profit_from_item": round(profit * sold, 2),
        }
