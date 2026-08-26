from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend import models, auth

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/")
def get_alerts(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    alerts = db.query(models.Alert).filter(
        models.Alert.owner_id == owner.id
    ).order_by(models.Alert.created_at.desc()).limit(50).all()

    return [
        {
            "id": a.id,
            "type": a.alert_type,
            "message": a.message,
            "is_read": a.is_read,
            "created_at": a.created_at,
        }
        for a in alerts
    ]


@router.put("/{alert_id}/read")
def mark_read(
    alert_id: int,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.owner_id == owner.id
    ).first()
    if alert:
        alert.is_read = True
        db.commit()
    return {"message": "Marked as read"}


@router.put("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    db.query(models.Alert).filter(
        models.Alert.owner_id == owner.id,
        models.Alert.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All alerts marked as read"}
