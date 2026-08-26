from sqlalchemy.orm import Session
from backend import models
from backend.services.claude_service import generate_offer_message


class MarketingAgent:
    def __init__(self, db: Session, owner_id: int):
        self.db = db
        self.owner_id = owner_id
        self.owner = db.query(models.Owner).filter(models.Owner.id == owner_id).first()

    def create_slow_stock_offer(self, item_name: str, days_since_sold: int, stock_qty: float) -> models.PendingAction:
        reason = f"Stock not moving for {days_since_sold} days, {stock_qty} units in stock"
        message = generate_offer_message(
            item_name=item_name,
            reason=reason,
            discount_pct=10,
            shop_name=self.owner.shop_name if self.owner else ""
        )

        action = models.PendingAction(
            owner_id=self.owner_id,
            action_type="send_whatsapp_offer",
            title=f"Slow stock offer: {item_name}",
            description=f"{item_name} hasn't sold in {days_since_sold} days. Offer generated to clear stock.",
            generated_content=message,
            action_data={
                "item_name": item_name,
                "phone": self.owner.whatsapp_number if self.owner else None,
                "reason": "slow_stock",
            },
            status="pending",
        )
        self.db.add(action)
        self.db.commit()
        return action

    def create_low_stock_reorder_reminder(self, item_name: str, qty_left: float) -> models.PendingAction:
        message = f"Heads up: {item_name} is running low ({qty_left} units left). Time to reorder from your supplier."

        action = models.PendingAction(
            owner_id=self.owner_id,
            action_type="reorder_reminder",
            title=f"Reorder: {item_name}",
            description=f"{item_name} stock is below threshold. Approve to send yourself a reminder.",
            generated_content=message,
            action_data={"item_name": item_name, "qty_left": qty_left},
            status="pending",
        )
        self.db.add(action)
        self.db.commit()
        return action

    def create_demand_fulfillment_alert(self, product_name: str, demand_count: int, customer_phones: list) -> models.PendingAction:
        message = generate_offer_message(
            item_name=product_name,
            reason=f"{demand_count} customers asked for this product",
            shop_name=self.owner.shop_name if self.owner else ""
        )

        action = models.PendingAction(
            owner_id=self.owner_id,
            action_type="notify_demand_customers",
            title=f"Notify customers: {product_name} now available",
            description=f"{demand_count} customers asked for {product_name}. Approve to notify them.",
            generated_content=message,
            action_data={"product_name": product_name, "phones": customer_phones},
            status="pending",
        )
        self.db.add(action)
        self.db.commit()
        return action
