"""
AI Agent Orchestrator — uses Gemini to REASON about business data.

The difference from rule-based agents:
  Rules: if qty < 10 → alert           (dumb, misses context)
  AI:    Gemini sees ALL data together → "Milk sales dropped 30% but you
          have 60 units in stock AND 5 customers asked for it on WhatsApp.
          Drop price by ₹2 to clear faster." (smart, contextual)

Gemini acts as the agent brain — it reads everything and decides
what matters most, what to do, and why.
"""
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend import models
from backend.services.claude_service import _call   # reuse the Gemini caller


class AgentOrchestrator:
    def __init__(self, db: Session, owner_id: int):
        self.db = db
        self.owner_id = owner_id

    # ─────────────────────────────────────────────────────────────────────────
    # DATA GATHERING  (pure DB reads, no AI yet)
    # ─────────────────────────────────────────────────────────────────────────

    def _gather_data(self) -> dict:
        now   = datetime.utcnow()
        d7    = now - timedelta(days=7)
        d30   = now - timedelta(days=30)

        inventory = self.db.query(models.Inventory).filter(
            models.Inventory.owner_id == self.owner_id
        ).all()

        sales_7d = self.db.query(models.Sale).filter(
            models.Sale.owner_id == self.owner_id,
            models.Sale.date >= d7
        ).all()

        expenses_30d = self.db.query(models.Expense).filter(
            models.Expense.owner_id == self.owner_id,
            models.Expense.date >= d30
        ).all()

        demand_signals = self.db.query(models.DemandSignal).filter(
            models.DemandSignal.owner_id == self.owner_id
        ).order_by(models.DemandSignal.count.desc()).limit(10).all()

        # Build compact summaries
        inv_lines = []
        for i in inventory:
            days_no_sale = None
            if i.last_sold_date:
                days_no_sale = (now - i.last_sold_date.replace(tzinfo=None)).days
            margin = round((i.selling_price - i.cost_price) / i.selling_price * 100, 1) if i.selling_price > 0 else 0
            inv_lines.append(
                f"{i.item_name}: stock={i.quantity}{i.unit}, cost=₹{i.cost_price}, "
                f"sell=₹{i.selling_price}, margin={margin}%, "
                f"threshold={i.low_stock_threshold}, "
                f"days_since_sold={days_no_sale if days_no_sale is not None else 'never'}"
            )

        # Sales velocity per item
        sales_map = {}
        total_revenue_7d = 0
        for s in sales_7d:
            sales_map[s.item_name] = sales_map.get(s.item_name, 0) + s.quantity_sold
            total_revenue_7d += s.total_amount

        sales_lines = [f"{k}: sold {v} units in 7 days" for k, v in
                       sorted(sales_map.items(), key=lambda x: -x[1])[:10]]

        demand_lines = [
            f"{d.product_name}: asked {d.count} times by customers"
            for d in demand_signals
        ]

        total_expenses_30d = sum(e.amount for e in expenses_30d)

        return {
            "inventory": inv_lines,
            "sales_7d": sales_lines,
            "total_revenue_7d": round(total_revenue_7d, 2),
            "total_expenses_30d": round(total_expenses_30d, 2),
            "demand_signals": demand_lines,
            "num_items": len(inventory),
            "low_stock_items": [i.item_name for i in inventory if i.quantity <= i.low_stock_threshold],
            "zero_stock_items": [i.item_name for i in inventory if i.quantity == 0],
        }

    # ─────────────────────────────────────────────────────────────────────────
    # THE AI AGENT  (Gemini reasons over all data)
    # ─────────────────────────────────────────────────────────────────────────

    def run_daily_check(self) -> dict:
        data = self._gather_data()

        prompt = f"""You are an AI business advisor agent for a small kirana/grocery shop.
Analyze ALL of this business data together and give specific, actionable insights.
Think holistically — not item by item. Look for patterns, risks and opportunities.

=== INVENTORY ({data['num_items']} items) ===
{chr(10).join(data['inventory']) or 'No inventory'}

=== SALES LAST 7 DAYS ===
Total revenue: ₹{data['total_revenue_7d']}
{chr(10).join(data['sales_7d']) or 'No sales recorded yet'}

=== MONTHLY EXPENSES ===
₹{data['total_expenses_30d']}

=== CUSTOMER DEMAND (items customers asked for on WhatsApp/chat) ===
{chr(10).join(data['demand_signals']) or 'No demand signals yet'}

=== CRITICAL ITEMS ===
Low stock (below threshold): {', '.join(data['low_stock_items']) or 'None'}
Zero stock: {', '.join(data['zero_stock_items']) or 'None'}

Now return ONLY valid JSON (no markdown, no explanation):
{{
  "alerts": [
    {{
      "type": "low_stock|dead_stock|loss_item|cash_warning|demand_gap|pricing",
      "item": "item name or null",
      "message": "specific alert message with numbers",
      "urgency": "high|medium|low"
    }}
  ],
  "actions": [
    {{
      "type": "reorder|discount|price_change|stock_new_item|send_offer",
      "item": "item name or null",
      "message": "exact action to take with specific numbers",
      "suggested_value": null
    }}
  ],
  "daily_insight": "2-3 sentences: what is the MOST IMPORTANT thing happening in this business right now and the ONE thing the owner should do today",
  "top_opportunity": "One specific money-making opportunity the owner is missing",
  "top_risk": "One specific risk that could hurt profits this week"
}}

Rules:
- Max 4 alerts, max 4 actions
- Be SPECIFIC: say "Milk (32 units, sells 18/day — will run out in 2 days)" not "Milk is low"
- If no data yet, give general startup advice
- Prioritize by business impact, not alphabetically"""

        results = {"alerts_created": 0, "actions_created": 0, "insights": []}

        try:
            raw = _call(prompt, max_tokens=1200)

            # Strip markdown fences if present
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    part = part.strip().lstrip("json").strip()
                    if part.startswith("{"):
                        raw = part
                        break

            analysis = json.loads(raw.strip())

        except Exception as e:
            print(f"[Agent] Gemini analysis failed: {e}")
            # Fallback to simple rule-based check
            analysis = self._fallback_rules(data)

        # ── Save alerts to DB ──
        for alert_data in analysis.get("alerts", []):
            alert = models.Alert(
                owner_id=self.owner_id,
                alert_type=alert_data.get("type", "info"),
                message=f"[{alert_data.get('urgency','medium').upper()}] {alert_data.get('message', '')}",
            )
            self.db.add(alert)
            results["alerts_created"] += 1

        # ── Save actions to DB ──
        for action_data in analysis.get("actions", []):
            atype = action_data.get("type", "general")
            item  = action_data.get("item") or "General"
            title_map = {
                "reorder":       f"Reorder: {item}",
                "discount":      f"Discount: {item}",
                "price_change":  f"Price Change: {item}",
                "stock_new_item":f"Stock New Item: {item}",
                "send_offer":    f"Send Offer: {item}",
            }
            action = models.PendingAction(
                owner_id=self.owner_id,
                action_type=atype,
                title=title_map.get(atype, f"AI Suggestion: {item}"),
                description=action_data.get("message", ""),
                action_data={
                    "item_name": action_data.get("item"),
                    "suggested_value": action_data.get("suggested_value"),
                    "ai_generated": True,
                },
                status="pending",
            )
            self.db.add(action)
            results["actions_created"] += 1

        # ── Save daily insight as alert ──
        insight     = analysis.get("daily_insight", "")
        opportunity = analysis.get("top_opportunity", "")
        risk        = analysis.get("top_risk", "")

        if insight:
            full_insight = insight
            if opportunity:
                full_insight += f"\n\nOpportunity: {opportunity}"
            if risk:
                full_insight += f"\n\nRisk: {risk}"

            self.db.add(models.Alert(
                owner_id=self.owner_id,
                alert_type="daily_insight",
                message=full_insight,
            ))
            results["alerts_created"] += 1
            results["insights"].append(insight)

        self.db.commit()
        return results

    # ─────────────────────────────────────────────────────────────────────────
    # FALLBACK  (only used if Gemini fails — minimal rules)
    # ─────────────────────────────────────────────────────────────────────────

    def _fallback_rules(self, data: dict) -> dict:
        alerts, actions = [], []

        for item_name in data["low_stock_items"]:
            alerts.append({"type": "low_stock", "item": item_name,
                           "message": f"{item_name} is below minimum stock. Reorder soon.", "urgency": "high"})
            actions.append({"type": "reorder", "item": item_name,
                            "message": f"Reorder {item_name} — stock is critically low.", "suggested_value": None})

        if data["total_expenses_30d"] > 0 and data["total_revenue_7d"] * 4 < data["total_expenses_30d"]:
            alerts.append({"type": "cash_warning", "item": None,
                           "message": "Monthly expenses may exceed revenue. Review pricing.", "urgency": "high"})

        for demand in data["demand_signals"][:2]:
            actions.append({"type": "stock_new_item", "item": demand.split(":")[0],
                            "message": f"Customers are asking for {demand.split(':')[0]} — consider stocking it.",
                            "suggested_value": None})

        return {
            "alerts": alerts,
            "actions": actions,
            "daily_insight": "Run AI Check regularly to get intelligent insights about your business.",
            "top_opportunity": "Add items that customers are requesting but you don't stock yet.",
            "top_risk": "Check if any items are selling at a loss (selling price < cost price).",
        }
