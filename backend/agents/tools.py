"""
Agent Tools & Verification Engine — Session 2 of Course Framework.

Concepts:
- Tool Definitions & Execution Patterns
- Verification & Safety Approvals
- Consequential Action Gating (creates PendingAction if high-risk)
"""
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models


class AgentToolRegistry:
    def __init__(self, db: Session, owner_id: int):
        self.db = db
        self.owner_id = owner_id

    def execute_tool(self, intent: str, entities: Dict[str, Any], grounded_context: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Executes or gates actions based on verification rules.
        Returns: (result_dict, human_readable_summary)
        """
        if intent == "ACTION_UPDATE_PRICE":
            return self._tool_update_price(entities, grounded_context)
        elif intent == "ACTION_ADJUST_STOCK":
            return self._tool_adjust_stock(entities, grounded_context)
        elif intent == "ACTION_RECORD_SALE":
            return self._tool_record_sale(entities, grounded_context)
        elif intent == "ACTION_RECORD_EXPENSE":
            return self._tool_record_expense(entities)
        else:
            return {"status": "noop"}, "No modifying tool required."

    def _tool_update_price(self, entities: Dict[str, Any], grounded: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        item_name = entities.get("item_name")
        new_price = entities.get("price")
        if not item_name or new_price is None:
            return {"error": "Missing item_name or price"}, "Failed: incomplete parameters."

        item = self.db.query(models.Inventory).filter(
            models.Inventory.owner_id == self.owner_id,
            func.lower(models.Inventory.item_name) == item_name.lower().strip()
        ).first()

        if not item:
            return {"error": f"Item '{item_name}' not found in inventory."}, f"Item '{item_name}' does not exist."

        # Consequential Verification Rule:
        # If selling price is reduced below cost price, gate it behind PendingAction approval!
        if new_price < item.cost_price:
            pending = models.PendingAction(
                owner_id=self.owner_id,
                action_type="risky_price_drop",
                title=f"Approval Needed: Sell {item.item_name} at a Loss?",
                description=(
                    f"Requested price ₹{new_price} is LOWER than your cost price (₹{item.cost_price}). "
                    f"This will result in a loss of ₹{round(item.cost_price - new_price, 2)} per unit."
                ),
                generated_content=f"Warning: Negative margin detected for {item.item_name}.",
                action_data={"item_id": item.id, "item_name": item.item_name, "proposed_price": new_price, "cost_price": item.cost_price},
                status="pending"
            )
            self.db.add(pending)
            self.db.commit()
            return {
                "action": "gated_for_approval",
                "pending_action_id": pending.id,
                "reason": "Selling price lower than cost price (Negative Margin Risk)"
            }, f"⚠️ Safety Hold: Proposed price ₹{new_price} is below your cost price (₹{item.cost_price}). Awaiting your approval on the dashboard."

        old_price = item.selling_price
        item.selling_price = float(new_price)
        self.db.commit()
        return {
            "action": "price_updated",
            "item": item.item_name,
            "old_price": old_price,
            "new_price": new_price,
            "verified": True
        }, f"✅ Updated {item.item_name} selling price from ₹{old_price} to ₹{new_price}."

    def _tool_adjust_stock(self, entities: Dict[str, Any], grounded: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        item_name = entities.get("item_name")
        qty = entities.get("quantity")
        cost = entities.get("price")
        unit = entities.get("unit") or "units"

        if not item_name or qty is None:
            return {"error": "Missing item_name or quantity"}, "Failed: incomplete parameters."

        item = self.db.query(models.Inventory).filter(
            models.Inventory.owner_id == self.owner_id,
            func.lower(models.Inventory.item_name) == item_name.lower().strip()
        ).first()

        if item:
            item.quantity += float(qty)
            if cost is not None:
                item.cost_price = float(cost)
            self.db.commit()
            return {
                "action": "stock_added",
                "item": item.item_name,
                "added_qty": qty,
                "current_stock": item.quantity,
                "verified": True
            }, f"✅ Added {qty} {item.unit} to {item.item_name}. New stock: {item.quantity} {item.unit}."
        else:
            # Create new inventory item
            cost_val = float(cost) if cost else 0.0
            selling_val = round(cost_val * 1.3, 2) if cost_val > 0 else 0.0
            new_item = models.Inventory(
                owner_id=self.owner_id,
                item_name=item_name.strip(),
                quantity=float(qty),
                unit=unit,
                cost_price=cost_val,
                selling_price=selling_val,
                low_stock_threshold=10
            )
            self.db.add(new_item)
            self.db.commit()
            return {
                "action": "new_item_created",
                "item": new_item.item_name,
                "quantity": qty,
                "cost_price": cost_val,
                "verified": True
            }, f"✅ Created new item {new_item.item_name} with {qty} {unit} stock."

    def _tool_record_sale(self, entities: Dict[str, Any], grounded: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        item_name = entities.get("item_name")
        qty = entities.get("quantity") or 1.0

        item = self.db.query(models.Inventory).filter(
            models.Inventory.owner_id == self.owner_id,
            func.lower(models.Inventory.item_name) == (item_name or "").lower().strip()
        ).first()

        if not item:
            return {"error": f"Item '{item_name}' not found"}, f"Cannot record sale: '{item_name}' not found in inventory."

        sell_price = float(entities.get("price") or item.selling_price)
        total = sell_price * float(qty)

        sale = models.Sale(
            owner_id=self.owner_id,
            item_name=item.item_name,
            quantity_sold=float(qty),
            selling_price=sell_price,
            total_amount=total
        )
        item.quantity = max(0.0, item.quantity - float(qty))
        item.last_sold_date = func.now()
        self.db.add(sale)
        self.db.commit()

        return {
            "action": "sale_recorded",
            "item": item.item_name,
            "quantity_sold": qty,
            "total_amount": total,
            "remaining_stock": item.quantity,
            "verified": True
        }, f"✅ Recorded sale: {qty} {item.unit} of {item.item_name} for ₹{total}. (Stock left: {item.quantity})"

    def _tool_record_expense(self, entities: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        amount = entities.get("expense_amount") or entities.get("price")
        exp_type = entities.get("expense_type") or "other"

        if not amount:
            return {"error": "Missing expense amount"}, "Failed: specify amount."

        expense = models.Expense(
            owner_id=self.owner_id,
            amount=float(amount),
            expense_type=str(exp_type).lower(),
            description=f"Recorded via AI Agent"
        )
        self.db.add(expense)
        self.db.commit()

        return {
            "action": "expense_recorded",
            "amount": amount,
            "type": exp_type,
            "verified": True
        }, f"✅ Recorded {exp_type} expense of ₹{amount}."
