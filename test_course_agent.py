"""
Verification script for Course Sessions 1, 2, 3 Agent Architecture.
"""
import sys
from backend.database import SessionLocal
from backend import models
from backend.agents.intent_router import IntentRouter
from backend.agents.tools import AgentToolRegistry

def test_course_agent_pipeline():
    db = SessionLocal()
    try:
        # Find or create a test owner
        owner = db.query(models.Owner).first()
        if not owner:
            print("[SKIP] No owner found in database to test with.")
            return

        print(f"Testing with Owner ID {owner.id} ({owner.name} - {owner.shop_name})")

        # ── Test 1: Session 1 (Decomposition & Ambiguity Detection) ──
        router = IntentRouter(db, owner.id)
        ambiguous_input = "Can you update the price?"
        decomp = router.decompose(ambiguous_input)
        print("\n--- Test 1: Ambiguity Detection ---")
        print(f"Input: '{ambiguous_input}'")
        print(f"Detected Intent: {decomp.get('intent')}")
        print(f"Clarification Question: {decomp.get('clarification_question')}")
        assert decomp.get("intent") == "AMBIGUOUS" or decomp.get("clarification_question") is not None, "Failed ambiguity detection"

        # ── Test 2: Session 3 (Source Authority Grounding) ──
        # Create a sample test item if none exists
        test_item = db.query(models.Inventory).filter(models.Inventory.owner_id == owner.id).first()
        if not test_item:
            test_item = models.Inventory(
                owner_id=owner.id,
                item_name="Nandini Milk 500ml",
                quantity=20,
                unit="packets",
                cost_price=22.0,
                selling_price=24.0,
                low_stock_threshold=5
            )
            db.add(test_item)
            db.commit()

        grounded = router.ground_context({"item_name": test_item.item_name})
        print("\n--- Test 2: Source Authority Grounding ---")
        print(f"Item: {test_item.item_name}")
        print(f"Grounded Record: {grounded.get('item_record')}")
        assert grounded.get("item_record") is not None, "Grounding failed to find item"

        # ── Test 3: Session 2 (Consequential Safety Gate) ──
        tools = AgentToolRegistry(db, owner.id)
        # Attempt to drop selling price to 1.0 (which is less than cost 3.25)
        res, summary = tools.execute_tool(
            intent="ACTION_UPDATE_PRICE",
            entities={"item_name": test_item.item_name, "price": 1.0},
            grounded_context=grounded
        )
        print("\n--- Test 3: Consequential Safety Gate (Selling at a Loss) ---")
        print(f"Tool Output: {res}")
        print(f"Summary: {summary.encode('ascii', 'replace').decode('ascii')}")
        assert res.get("action") == "gated_for_approval", "Failed to gate loss-making price change"

        # Verify PendingAction was created in SQLite
        pending = db.query(models.PendingAction).filter(
            models.PendingAction.owner_id == owner.id,
            models.PendingAction.action_type == "risky_price_drop"
        ).order_by(models.PendingAction.id.desc()).first()
        print(f"Created Pending Action in DB: ID={pending.id}, Title='{pending.title}'")
        assert pending is not None, "Pending action record not found in DB"

        # ── Test 4: Session 2 (Safe Tool Execution) ──
        res_safe, summary_safe = tools.execute_tool(
            intent="ACTION_UPDATE_PRICE",
            entities={"item_name": test_item.item_name, "price": 6.0},
            grounded_context=grounded
        )
        print("\n--- Test 4: Safe Tool Execution (Valid Price) ---")
        print(f"Tool Output: {res_safe}")
        print(f"Summary: {summary_safe.encode('ascii', 'replace').decode('ascii')}")
        assert res_safe.get("verified") is True, "Safe update failed"
        assert res_safe.get("new_price") == 6.0, "Price was not updated"

        print("\nALL 4 COURSE CONCEPTS VERIFIED SUCCESSFULLY!")

    finally:
        db.close()

if __name__ == "__main__":
    test_course_agent_pipeline()
