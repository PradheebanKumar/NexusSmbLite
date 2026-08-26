from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.database import SessionLocal
from backend import models
from backend.agents.orchestrator import AgentOrchestrator

scheduler = BackgroundScheduler()


def run_daily_agent_check():
    """Runs every evening at 8 PM for all owners."""
    db = SessionLocal()
    try:
        owners = db.query(models.Owner).all()
        for owner in owners:
            try:
                orchestrator = AgentOrchestrator(db, owner.id)
                result = orchestrator.run_daily_check()
                print(f"[Scheduler] Daily check for owner {owner.id} ({owner.shop_name}): {result}")
            except Exception as e:
                print(f"[Scheduler] Error for owner {owner.id}: {e}")
    finally:
        db.close()


def run_stock_monitor():
    """Runs every 6 hours to check for critical stock levels."""
    db = SessionLocal()
    try:
        owners = db.query(models.Owner).all()
        for owner in owners:
            try:
                from backend.agents.inventory_agent import InventoryAgent
                agent = InventoryAgent(db, owner.id)
                low_stock = agent.detect_low_stock()
                for item in low_stock:
                    # Only create alert if not already created today
                    from datetime import datetime, timedelta
                    recent = db.query(models.Alert).filter(
                        models.Alert.owner_id == owner.id,
                        models.Alert.alert_type == "low_stock",
                        models.Alert.message.contains(item["item"]),
                        models.Alert.created_at >= datetime.utcnow() - timedelta(hours=12)
                    ).first()
                    if not recent:
                        alert = models.Alert(
                            owner_id=owner.id,
                            alert_type="low_stock",
                            message=item["message"],
                        )
                        db.add(alert)
                db.commit()
            except Exception as e:
                print(f"[StockMonitor] Error for owner {owner.id}: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        run_daily_agent_check,
        CronTrigger(hour=20, minute=0),  # 8 PM daily
        id="daily_check",
        replace_existing=True,
    )
    scheduler.add_job(
        run_stock_monitor,
        CronTrigger(hour="*/6"),  # every 6 hours
        id="stock_monitor",
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] Started — daily check at 8 PM, stock monitor every 6 hours")


def stop_scheduler():
    scheduler.shutdown()
