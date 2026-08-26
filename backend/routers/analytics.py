from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
from pydantic import BaseModel
import json
from backend.database import get_db
from backend import models, auth
from backend.services.claude_service import _call

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ── Profit & Loss ─────────────────────────────────────────────────────────────
@router.get("/profit-loss")
def get_profit_loss(
    days: int = 30,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    since = datetime.utcnow() - timedelta(days=days)
    sales    = db.query(models.Sale).filter(models.Sale.owner_id == owner.id, models.Sale.date >= since).all()
    expenses = db.query(models.Expense).filter(models.Expense.owner_id == owner.id, models.Expense.date >= since).all()

    total_revenue   = sum(s.total_amount for s in sales)
    total_expenses  = sum(e.amount for e in expenses)
    inventory       = {i.item_name.lower(): i.cost_price for i in db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id).all()}
    cogs            = sum(inventory.get(s.item_name.lower(), 0) * s.quantity_sold for s in sales)
    gross_profit    = total_revenue - cogs
    net_profit      = gross_profit - total_expenses

    return {
        "period_days": days,
        "total_revenue": round(total_revenue, 2),
        "cost_of_goods_sold": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "total_expenses": round(total_expenses, 2),
        "net_profit": round(net_profit, 2),
        "profit_margin_pct": round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
        "is_profitable": net_profit > 0,
    }


# ── Daily Sales Trend ─────────────────────────────────────────────────────────
@router.get("/daily-trend")
def get_daily_trend(
    days: int = 14,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    """Returns day-by-day revenue, profit, transactions for the sparkline chart."""
    since = datetime.utcnow() - timedelta(days=days)
    sales = db.query(models.Sale).filter(
        models.Sale.owner_id == owner.id,
        models.Sale.date >= since
    ).all()
    inv_map = {i.item_name.lower(): i.cost_price for i in
               db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id).all()}

    by_day = defaultdict(lambda: {"revenue": 0, "cogs": 0, "count": 0})
    for s in sales:
        day = s.date.strftime("%d %b")
        by_day[day]["revenue"] += s.total_amount
        by_day[day]["cogs"]    += inv_map.get(s.item_name.lower(), 0) * s.quantity_sold
        by_day[day]["count"]   += 1

    # Fill all days (including zero-sales days)
    result = []
    for i in range(days):
        d = datetime.utcnow() - timedelta(days=days - 1 - i)
        key = d.strftime("%d %b")
        row = by_day.get(key, {"revenue": 0, "cogs": 0, "count": 0})
        result.append({
            "day": key,
            "revenue": round(row["revenue"], 2),
            "profit": round(row["revenue"] - row["cogs"], 2),
            "transactions": row["count"],
        })
    return result


# ── Expense Breakdown ─────────────────────────────────────────────────────────
@router.get("/expense-breakdown")
def get_expense_breakdown(
    days: int = 30,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    since = datetime.utcnow() - timedelta(days=days)
    expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == owner.id,
        models.Expense.date >= since
    ).all()
    by_type = defaultdict(float)
    for e in expenses:
        by_type[e.expense_type] += e.amount
    total = sum(by_type.values())
    return {
        "total": round(total, 2),
        "breakdown": [
            {"type": k, "amount": round(v, 2), "pct": round(v / total * 100, 1) if total > 0 else 0}
            for k, v in sorted(by_type.items(), key=lambda x: -x[1])
        ]
    }


# ── Business Health Score ─────────────────────────────────────────────────────
@router.get("/health-score")
def get_health_score(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    """
    Composite 0-100 score across 5 dimensions:
    1. Profitability  (net margin %)
    2. Sales velocity (are you growing or declining?)
    3. Inventory health (low stock + dead stock)
    4. Cash flow (revenue vs expenses)
    5. Demand signals (how many customers are asking for things you don't have)
    """
    now   = datetime.utcnow()
    m_ago = now - timedelta(days=30)
    w_ago = now - timedelta(days=7)

    inventory = db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id).all()
    sales_30d  = db.query(models.Sale).filter(models.Sale.owner_id == owner.id, models.Sale.date >= m_ago).all()
    sales_7d   = db.query(models.Sale).filter(models.Sale.owner_id == owner.id, models.Sale.date >= w_ago).all()
    expenses   = db.query(models.Expense).filter(models.Expense.owner_id == owner.id, models.Expense.date >= m_ago).all()
    demands    = db.query(models.DemandSignal).filter(models.DemandSignal.owner_id == owner.id).all()

    inv_map        = {i.item_name.lower(): i.cost_price for i in inventory}
    revenue_30d    = sum(s.total_amount for s in sales_30d)
    cogs_30d       = sum(inv_map.get(s.item_name.lower(), 0) * s.quantity_sold for s in sales_30d)
    expense_total  = sum(e.amount for e in expenses)
    net_profit_30d = revenue_30d - cogs_30d - expense_total
    revenue_7d     = sum(s.total_amount for s in sales_7d)

    # ── 1. Profitability score (0-25) ─────────────────────────────────────────
    margin = (net_profit_30d / revenue_30d * 100) if revenue_30d > 0 else 0
    profit_score = min(25, max(0, margin * 1.25))  # 20% margin = full 25pts

    # ── 2. Sales trend score (0-20) ───────────────────────────────────────────
    # Compare last 7d vs preceding 7d
    prev_7_start = now - timedelta(days=14)
    prev_7_end   = now - timedelta(days=7)
    prev_sales   = db.query(models.Sale).filter(
        models.Sale.owner_id == owner.id,
        models.Sale.date >= prev_7_start,
        models.Sale.date < prev_7_end,
    ).all()
    prev_rev = sum(s.total_amount for s in prev_sales)
    if prev_rev > 0:
        growth = (revenue_7d - prev_rev) / prev_rev * 100
        trend_score = min(20, max(0, 10 + growth * 0.5))  # flat = 10, +20% = 20, -20% = 0
    else:
        trend_score = 10  # neutral if no history

    # ── 3. Inventory health score (0-20) ─────────────────────────────────────
    if inventory:
        low_stock_pct  = sum(1 for i in inventory if i.quantity <= i.low_stock_threshold) / len(inventory)
        dead_stock_pct = sum(1 for i in inventory if i.last_sold_date and
                             (now - i.last_sold_date.replace(tzinfo=None)).days > 14) / len(inventory)
        inv_score = 20 * (1 - (low_stock_pct * 0.5 + dead_stock_pct * 0.5))
    else:
        inv_score = 0

    # ── 4. Cash flow score (0-20) ─────────────────────────────────────────────
    daily_rev = revenue_30d / 30
    daily_exp = expense_total / 30
    if daily_exp > 0:
        cover_ratio = daily_rev / daily_exp
        cash_score  = min(20, max(0, cover_ratio * 10))
    else:
        cash_score = 20 if revenue_30d > 0 else 5

    # ── 5. Demand fulfilment score (0-15) ─────────────────────────────────────
    hot_demands = sum(1 for d in demands if d.count >= 3)
    demand_score = max(0, 15 - hot_demands * 3)  # each unmet demand = -3pts

    total = round(profit_score + trend_score + inv_score + cash_score + demand_score)
    total = min(100, max(0, total))

    if total >= 75:   grade, color, summary = "A",  "green",  "Shop is running well. Keep it up!"
    elif total >= 55: grade, color, summary = "B",  "blue",   "Good overall — a few areas to improve."
    elif total >= 35: grade, color, summary = "C",  "yellow", "Needs attention in a few key areas."
    else:             grade, color, summary = "D",  "red",    "Immediate action needed to stay profitable."

    return {
        "score": total,
        "grade": grade,
        "color": color,
        "summary": summary,
        "dimensions": {
            "profitability":  round(profit_score, 1),
            "sales_trend":    round(trend_score, 1),
            "inventory":      round(inv_score, 1),
            "cash_flow":      round(cash_score, 1),
            "demand_match":   round(demand_score, 1),
        },
        "max_scores": {"profitability": 25, "sales_trend": 20, "inventory": 20, "cash_flow": 20, "demand_match": 15},
        "tips": _health_tips(profit_score, trend_score, inv_score, cash_score, demand_score, hot_demands),
    }


def _health_tips(profit, trend, inv, cash, demand, hot_demands):
    tips = []
    if profit < 12:
        tips.append({"area": "Profitability", "tip": "Your margins are thin. Use Revenue Advisor to find price increase opportunities.", "priority": "high"})
    if trend < 8:
        tips.append({"area": "Sales Trend", "tip": "Sales are declining week-on-week. Try running a discount offer or WhatsApp promotion.", "priority": "high"})
    if inv < 12:
        tips.append({"area": "Inventory", "tip": "Too many low-stock or dead-stock items. Restock fast movers and clear slow ones.", "priority": "medium"})
    if cash < 10:
        tips.append({"area": "Cash Flow", "tip": "Revenue barely covers expenses. Find at least one cost to reduce or one item to promote.", "priority": "high"})
    if hot_demands > 0:
        tips.append({"area": "Demand Gap", "tip": f"{hot_demands} products are being requested by multiple customers but you don't stock them. Add them!", "priority": "medium"})
    if not tips:
        tips.append({"area": "All Good", "tip": "Shop is healthy! Focus on growing — try a WhatsApp promotion or stocking a new popular product.", "priority": "low"})
    return tips


# ── Apply Price by Item Name ──────────────────────────────────────────────────
class PatchPriceRequest(BaseModel):
    item_name: str
    selling_price: float


@router.post("/apply-price")
def apply_price(
    req: PatchPriceRequest,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    """Apply a price change by item name — used by Revenue Advisor 'Apply' buttons."""
    item = db.query(models.Inventory).filter(
        models.Inventory.owner_id == owner.id,
        func.lower(models.Inventory.item_name) == req.item_name.lower()
    ).first()
    if not item:
        return {"ok": False, "error": f"Item '{req.item_name}' not found in inventory"}
    old_price = item.selling_price
    item.selling_price = round(req.selling_price, 2)
    db.commit()
    return {"ok": True, "item": item.item_name, "old_price": old_price, "new_price": item.selling_price}


# ── Stock Recovery / Break-Even ───────────────────────────────────────────────
@router.get("/break-even")
def get_break_even(
    item_name: Optional[str] = None,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    since = datetime.utcnow() - timedelta(days=30)
    monthly_expenses = sum(
        e.amount for e in db.query(models.Expense).filter(
            models.Expense.owner_id == owner.id, models.Expense.date >= since).all()
    )
    inventory = db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id)
    if item_name:
        inventory = inventory.filter(func.lower(models.Inventory.item_name) == item_name.lower())
    items = inventory.all()

    total_sales_30d  = db.query(models.Sale).filter(models.Sale.owner_id == owner.id, models.Sale.date >= since).all()
    avg_daily_revenue = sum(s.total_amount for s in total_sales_30d) / 30
    daily_breakeven   = monthly_expenses / 30

    results = []
    for item in items:
        profit_per_unit = item.selling_price - item.cost_price
        margin_pct      = (profit_per_unit / item.selling_price * 100) if item.selling_price > 0 else 0
        sold_30d        = sum(s.quantity_sold for s in db.query(models.Sale).filter(
            models.Sale.owner_id == owner.id,
            func.lower(models.Sale.item_name) == item.item_name.lower(),
            models.Sale.date >= since).all())
        stock_investment = round(item.cost_price * item.quantity, 2)
        potential_profit = round(profit_per_unit * item.quantity, 2)
        roi_pct          = round((potential_profit / stock_investment * 100) if stock_investment > 0 else 0, 1)

        if profit_per_unit <= 0:
            results.append({
                "item": item.item_name, "unit": item.unit,
                "cost_price": item.cost_price, "selling_price": item.selling_price,
                "profit_per_unit": round(profit_per_unit, 2), "margin_pct": round(margin_pct, 1),
                "stock_investment": stock_investment, "potential_profit": 0, "roi_pct": 0,
                "units_to_recover": None, "sold_this_month": round(sold_30d, 1),
                "current_quantity": item.quantity, "pct_recovered": 0,
                "insight": f"Selling at a LOSS! Raise price above Rs.{item.cost_price} immediately.",
                "status": "loss"
            })
            continue

        units_to_recover = round(stock_investment / profit_per_unit, 1)
        pct_recovered    = min(100, round((sold_30d / units_to_recover * 100) if units_to_recover > 0 else 100, 1))
        remaining        = max(0, units_to_recover - sold_30d)

        if sold_30d >= units_to_recover:
            insight = f"Investment recovered! Rs.{round((sold_30d - units_to_recover) * profit_per_unit)} pure profit earned."
            status  = "profit"
        elif remaining <= units_to_recover * 0.25:
            insight = f"Almost there! Sell {round(remaining)} more {item.unit} to recover your Rs.{stock_investment} investment."
            status  = "close"
        else:
            insight = f"Invested Rs.{stock_investment} in stock. Need to sell {round(units_to_recover)} {item.unit} total. {round(sold_30d)} sold so far."
            status  = "below"

        results.append({
            "item": item.item_name, "unit": item.unit,
            "cost_price": item.cost_price, "selling_price": item.selling_price,
            "profit_per_unit": round(profit_per_unit, 2), "margin_pct": round(margin_pct, 1),
            "stock_investment": stock_investment, "potential_profit": potential_profit,
            "roi_pct": roi_pct, "units_to_recover": units_to_recover,
            "sold_this_month": round(sold_30d, 1), "current_quantity": round(item.quantity, 1),
            "pct_recovered": pct_recovered, "insight": insight, "status": status,
        })

    return {
        "monthly_fixed_costs": round(monthly_expenses, 2),
        "daily_breakeven_revenue": round(daily_breakeven, 2),
        "avg_daily_revenue": round(avg_daily_revenue, 2),
        "shop_is_covering_costs": avg_daily_revenue >= daily_breakeven,
        "items": sorted(results, key=lambda x: x["pct_recovered"], reverse=True),
    }


# ── Revenue Advisor ───────────────────────────────────────────────────────────
class RevenueGoalRequest(BaseModel):
    revenue_gap: float
    reason: Optional[str] = ""


@router.post("/revenue-advisor")
def revenue_advisor(
    req: RevenueGoalRequest,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    since = datetime.utcnow() - timedelta(days=30)
    inventory  = db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id).all()
    sales_30d  = db.query(models.Sale).filter(models.Sale.owner_id == owner.id, models.Sale.date >= since).all()
    month_revenue = sum(s.total_amount for s in sales_30d)
    month_expenses = sum(e.amount for e in db.query(models.Expense).filter(
        models.Expense.owner_id == owner.id, models.Expense.date >= since).all())

    # Sales velocity per item
    velocity = defaultdict(float)
    for s in sales_30d:
        velocity[s.item_name.lower()] += s.quantity_sold

    # Build rich item data — include item ID so frontend can apply prices
    items_data = []
    for i in inventory:
        vel    = velocity.get(i.item_name.lower(), 0)
        margin = round((i.selling_price - i.cost_price) / i.selling_price * 100, 1) if i.selling_price > 0 else 0
        days_no_sale = None
        if i.last_sold_date:
            days_no_sale = (datetime.utcnow() - i.last_sold_date.replace(tzinfo=None)).days
        items_data.append({
            "id": i.id,          # ← always include so Apply button works
            "name": i.item_name,
            "cost": i.cost_price,
            "sell": i.selling_price,
            "margin_pct": margin,
            "stock": i.quantity,
            "unit": i.unit,
            "sold_30d": vel,
            "days_since_sold": days_no_sale,
            "monthly_revenue": round(vel * i.selling_price, 2),
        })

    items_data.sort(key=lambda x: -x["sold_30d"])

    # Also pull demand signals for context
    demand_signals = db.query(models.DemandSignal).filter(
        models.DemandSignal.owner_id == owner.id,
        models.DemandSignal.count >= 2,
    ).order_by(models.DemandSignal.count.desc()).limit(5).all()
    demand_text = ", ".join(f"{d.product_name} ({d.count} requests)" for d in demand_signals) or "None"

    # No inventory at all → early return
    if not inventory:
        return {
            "revenue_gap": req.revenue_gap, "current_monthly_revenue": 0,
            "target_revenue": req.revenue_gap, "actions": [],
            "total_expected_gain": 0,
            "summary": "Add your products to inventory first, then run this again.",
            "warning": "No inventory found. Go to Inventory page and add your products.",
        }

    # Build a compact, readable table for Gemini
    table_lines = []
    for it in items_data[:20]:
        profit_u = round(it["sell"] - it["cost"], 2)
        days_lbl = f"{it['days_since_sold']}d ago" if it["days_since_sold"] is not None else "never sold"
        table_lines.append(
            f"- {it['name']}: sell=Rs.{it['sell']}, cost=Rs.{it['cost']}, "
            f"profit/unit=Rs.{profit_u}, sold_30d={int(it['sold_30d'])}, "
            f"stock={it['stock']}{it['unit']}, last_sale={days_lbl}"
        )
    table_str = "\n".join(table_lines)

    no_sales = month_revenue == 0
    sales_note = (
        "NOTE: No sales recorded yet — base suggestions on inventory margins and stock levels."
        if no_sales else
        f"Revenue this month so far: Rs.{round(month_revenue)}, expenses: Rs.{round(month_expenses)}"
    )

    prompt = f"""You are a sharp, practical revenue advisor for "{owner.shop_name}", a small Indian kirana shop.
The owner needs Rs.{round(req.revenue_gap)} MORE revenue{f' — reason: {req.reason}' if req.reason else ''}.

{sales_note}

PRODUCT DATA:
{table_str}

CUSTOMER DEMAND (products customers asked for but may not be in stock):
{demand_text}

YOUR JOB: Give 3-5 SPECIFIC actions that together will generate approximately Rs.{round(req.revenue_gap)} extra.

RULES FOR CHOOSING ACTIONS:
- price_increase: Pick items with sold_30d > 5 (proven sellers). Increase by Rs.1-5 only.
  Math: extra_revenue = (new_price - old_price) × sold_30d
  Example: Milk sells 60L/month at Rs.26. Raise to Rs.27 = Rs.1 × 60 = Rs.60 extra.

- discount: Items not sold in 7+ days with stock > 0. Price near cost+5% to recover cash fast.
  Math: extra_revenue = discounted_price × units_likely_to_sell (estimate 30% of stock)

- promote: Fast sellers with good margin — push via WhatsApp offer to sell more volume.
  Math: extra_revenue = profit_per_unit × expected_extra_units (estimate 20% volume increase)

- stock_new: Demand signals show customers want X but you don't have it — stock it.
  Math: extra_revenue = estimated_selling_price × estimated_weekly_demand × 4

IMPORTANT: Use real numbers from the data. Show exact calculation in the reason field.
Total of all expected_extra_revenue should add up to approximately Rs.{round(req.revenue_gap)}.

Return ONLY this JSON (no markdown):
{{
  "revenue_gap": {req.revenue_gap},
  "current_monthly_revenue": {round(month_revenue, 2)},
  "target_revenue": {round(month_revenue + req.revenue_gap, 2)},
  "actions": [
    {{
      "rank": 1,
      "type": "price_increase|discount|promote|stock_new",
      "item": "exact product name",
      "item_id": 0,
      "current_price": 0.0,
      "suggested_price": 0.0,
      "reason": "e.g. Sells 60 units/month. Rs.1 increase × 60 units = Rs.60 extra this month.",
      "how_to": "One sentence on what owner should do RIGHT NOW",
      "expected_extra_revenue": 0.0,
      "confidence": "high|medium|low"
    }}
  ],
  "total_expected_gain": 0.0,
  "summary": "Plain English 2-sentence plan summary",
  "warning": "One risk or null"
}}"""

    result = None
    try:
        raw = _call(prompt, max_tokens=1800)
        if "```" in raw:
            for part in raw.split("```"):
                p = part.strip().lstrip("json").strip()
                if p.startswith("{"):
                    raw = p
                    break
        result = json.loads(raw.strip())
    except Exception as e:
        print(f"[RevenueAdvisor] Gemini failed: {e}, using fallback")
        result = _fallback_revenue_plan(items_data, req.revenue_gap, month_revenue)

    # Patch item_id into each action using the items_data lookup (in case AI returns 0)
    id_map = {i["name"].lower(): i["id"] for i in items_data}
    for action in result.get("actions", []):
        if not action.get("item_id"):
            action["item_id"] = id_map.get(action.get("item", "").lower(), 0)

    # Save as pending actions
    for action in result.get("actions", []):
        atype = "price_change" if action["type"] == "price_increase" else action["type"]
        type_label = {
            "price_change": "Price Change", "discount": "Discount / Clear Stock",
            "promote": "Promote Item", "upsell": "Upsell / Bundle", "stock_new": "Stock New Item",
        }.get(atype, atype)
        db.add(models.PendingAction(
            owner_id=owner.id,
            action_type=atype,
            title=f"{type_label}: {action.get('item', '')}",
            description=f"{action.get('reason','')} — Expected extra revenue: Rs.{action.get('expected_extra_revenue',0)}",
            action_data={
                "item_name": action.get("item"),
                "item_id": action.get("item_id", 0),
                "current_price": action.get("current_price", 0),
                "suggested_price": action.get("suggested_price", 0),
                "expected_gain": action.get("expected_extra_revenue", 0),
                "source": "revenue_advisor",
            },
            status="pending",
        ))
    db.commit()
    return result


def _fallback_revenue_plan(items_data, gap, current_revenue):
    """
    Smart fallback when Gemini fails or returns garbage.
    Logic:
      - Items with good sales (sold_30d >= 5) → small price increase (they can absorb it)
      - Items with ZERO sales and stock sitting unsold → DISCOUNT (convert dead stock to cash)
      - Items with some sales but slow → promote / slight discount
    """
    actions, gained = [], 0

    # ── 1. Best sellers → small price increase ────────────────────────────────
    for item in [i for i in items_data if i["sold_30d"] >= 5][:2]:
        increase = 2 if item["sell"] < 50 else 5
        extra    = round(increase * item["sold_30d"], 2)
        gained  += extra
        actions.append({
            "rank": len(actions) + 1,
            "type": "price_increase",
            "item": item["name"], "item_id": item["id"],
            "current_price": item["sell"],
            "suggested_price": round(item["sell"] + increase, 2),
            "reason": (
                f"Best seller — {int(item['sold_30d'])} units sold last 30 days. "
                f"Rs.{increase} increase × {int(item['sold_30d'])} units = +Rs.{extra}/month."
            ),
            "how_to": f"Go to Inventory, edit {item['name']}, change selling price to Rs.{item['sell'] + increase}.",
            "expected_extra_revenue": extra,
            "confidence": "high",
        })
        if gained >= gap:
            break

    # ── 2. Dead / slow stock → discount to clear cash ─────────────────────────
    dead_stock = [
        i for i in items_data
        if i["sold_30d"] == 0 and i["stock"] > 0
    ]
    for item in dead_stock[:3]:
        # Price it at cost + 8% — just enough margin to recover investment
        disc_price = round(max(item["cost"] * 1.08, item["sell"] * 0.80), 0)
        disc_price = max(disc_price, item["cost"] + 1)  # never go below cost
        units_likely_sold = min(item["stock"] * 0.4, 25)  # estimate 40% of stock sells at discount
        extra = round(disc_price * units_likely_sold, 2)
        gained += extra
        actions.append({
            "rank": len(actions) + 1,
            "type": "discount",
            "item": item["name"], "item_id": item["id"],
            "current_price": item["sell"],
            "suggested_price": disc_price,
            "reason": (
                f"This item has {item['stock']} {item['unit']} sitting unsold (0 sales in 30 days). "
                f"Discount to Rs.{disc_price} (8% above cost) → sell {round(units_likely_sold)} units = +Rs.{extra} cash recovered."
            ),
            "how_to": (
                f"Apply discount: change {item['name']} price to Rs.{disc_price}. "
                "It will automatically appear as a deal in your customer chat bot."
            ),
            "expected_extra_revenue": extra,
            "confidence": "medium",
        })
        if gained >= gap:
            break

    # ── 3. Slow sellers (some sales, not top) → promote ─────────────────────
    if gained < gap:
        slow = [i for i in items_data if 0 < i["sold_30d"] < 5][:2]
        for item in slow:
            extra_units = max(2, round(item["sold_30d"] * 0.3))
            extra = round(item["sell"] * extra_units, 2)
            gained += extra
            actions.append({
                "rank": len(actions) + 1,
                "type": "promote",
                "item": item["name"], "item_id": item["id"],
                "current_price": item["sell"],
                "suggested_price": item["sell"],
                "reason": (
                    f"{item['name']} sells {int(item['sold_30d'])} units/month — more customers don't know about it. "
                    f"Promoting could add {extra_units} more sales = +Rs.{extra}."
                ),
                "how_to": (
                    f"Tell customers about {item['name']} via the customer bot quick chips or "
                    "use Ad Generator to create a WhatsApp promotion."
                ),
                "expected_extra_revenue": extra,
                "confidence": "low",
            })

    # ── 4. Absolute fallback — no sales at all ────────────────────────────────
    if not actions:
        for item in items_data[:3]:
            disc_price = round(max(item["cost"] * 1.10, item["sell"] * 0.85), 0)
            extra = round(disc_price * 10, 2)
            gained += extra
            actions.append({
                "rank": len(actions) + 1,
                "type": "discount",
                "item": item["name"], "item_id": item["id"],
                "current_price": item["sell"],
                "suggested_price": disc_price,
                "reason": (
                    f"No sales recorded yet. Discount {item['name']} to Rs.{disc_price} to attract first customers. "
                    "Showing deals in your customer chat bot can bring walk-ins."
                ),
                "how_to": f"Apply this discount — it will automatically appear as a deal in your customer chat bot.",
                "expected_extra_revenue": extra,
                "confidence": "low",
            })

    # Assign sequential ranks
    for i, a in enumerate(actions):
        a["rank"] = i + 1

    total_gain = round(sum(a["expected_extra_revenue"] for a in actions), 2)
    return {
        "revenue_gap": gap,
        "current_monthly_revenue": current_revenue,
        "target_revenue": current_revenue + gap,
        "actions": actions,
        "total_expected_gain": total_gain,
        "summary": (
            f"Found {len(actions)} actions. Discounting unsold stock recovers cash fast; "
            f"price increases on best-sellers build long-term margin. "
            f"Total expected: +Rs.{round(total_gain)}."
        ),
        "warning": (
            "No recent sales data — all estimates. Apply discounts first to get cash flowing, "
            "then use Revenue Advisor again once you have 2+ weeks of sales."
            if current_revenue == 0 else
            "Estimates based on past 30 days. Monitor actual impact after each change."
        ),
    }


# ── Ad Generator ─────────────────────────────────────────────────────────────
class AdRequest(BaseModel):
    item_name: str
    ad_type: str = "whatsapp"
    offer_pct: Optional[float] = None
    custom_note: Optional[str] = None


@router.post("/generate-ad")
def generate_ad(
    req: AdRequest,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    item = db.query(models.Inventory).filter(
        models.Inventory.owner_id == owner.id,
        func.lower(models.Inventory.item_name) == req.item_name.lower()
    ).first()
    shop      = owner.shop_name
    item_info = f"{req.item_name} at Rs.{item.selling_price}/{item.unit}" if item else req.item_name
    offer_line = f"Special offer: {req.offer_pct}% off!" if req.offer_pct else "Fresh stock available!"

    type_instructions = {
        "whatsapp":       "Write a short WhatsApp message (2-3 lines). Casual, friendly, like a real shop owner texting customers. End with shop name.",
        "poster_caption": "Write a punchy poster caption (1 bold headline + 1 supporting line). Include price.",
        "sms":            "Write one SMS under 160 characters. Include item, price, shop name.",
    }

    prompt = f"""Generate a {req.ad_type} advertisement for a small Indian kirana shop.
Shop: {shop}
Product: {item_info}
{offer_line}
{f'Note: {req.custom_note}' if req.custom_note else ''}

{type_instructions.get(req.ad_type, type_instructions['whatsapp'])}

Rules: Real local shop owner tone, NOT corporate. Specific price. Max 3 lines for WhatsApp/SMS.
Return ONLY the ad text, nothing else."""

    try:
        ad_text = _call(prompt, max_tokens=200)
    except Exception:
        ad_text = f"{req.item_name} available at {shop}! {offer_line} Visit us today."

    type_label = {"whatsapp": "WhatsApp Message", "poster_caption": "Poster Caption", "sms": "SMS"}.get(req.ad_type, req.ad_type)
    db.add(models.PendingAction(
        owner_id=owner.id,
        action_type="send_whatsapp_offer",
        title=f"Ad Ready: {req.item_name} ({type_label})",
        description=f"AI-generated {type_label} for {req.item_name}. Copy and send to your customers.",
        generated_content=ad_text,
        action_data={"item_name": req.item_name, "ad_type": req.ad_type, "offer_pct": req.offer_pct, "ad_text": ad_text},
        status="pending",
    ))
    db.commit()
    return {"ad_text": ad_text, "type": req.ad_type, "item": req.item_name}


# ── Dashboard Summary ─────────────────────────────────────────────────────────
@router.get("/dashboard-summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    today_sales   = db.query(models.Sale).filter(models.Sale.owner_id == owner.id, models.Sale.date >= today_start).all()
    month_sales   = db.query(models.Sale).filter(models.Sale.owner_id == owner.id, models.Sale.date >= month_start).all()
    month_exp     = db.query(models.Expense).filter(models.Expense.owner_id == owner.id, models.Expense.date >= month_start).all()
    inventory     = db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id).all()
    pending       = db.query(models.PendingAction).filter(models.PendingAction.owner_id == owner.id, models.PendingAction.status == "pending").count()
    unread_alerts = db.query(models.Alert).filter(models.Alert.owner_id == owner.id, models.Alert.is_read == False).count()

    inv_map        = {i.item_name.lower(): i.cost_price for i in inventory}
    today_revenue  = sum(s.total_amount for s in today_sales)
    today_cogs     = sum(inv_map.get(s.item_name.lower(), 0) * s.quantity_sold for s in today_sales)
    month_revenue  = sum(s.total_amount for s in month_sales)
    month_exp_tot  = sum(e.amount for e in month_exp)
    month_cogs     = sum(inv_map.get(s.item_name.lower(), 0) * s.quantity_sold for s in month_sales)

    return {
        "today": {
            "revenue": round(today_revenue, 2),
            "profit": round(today_revenue - today_cogs, 2),
            "transactions": len(today_sales),
        },
        "this_month": {
            "revenue": round(month_revenue, 2),
            "expenses": round(month_exp_tot, 2),
            "net_profit": round(month_revenue - month_cogs - month_exp_tot, 2),
        },
        "inventory": {
            "total_items": len(inventory),
            "low_stock_count": sum(1 for i in inventory if i.quantity <= i.low_stock_threshold),
            "total_stock_value": round(sum(i.quantity * i.cost_price for i in inventory), 2),
        },
        "pending_actions": pending,
        "unread_alerts": unread_alerts,
    }
