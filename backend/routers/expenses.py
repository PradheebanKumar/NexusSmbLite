from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from backend.database import get_db
from backend import models, auth

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

EXPENSE_TYPES = ["rent", "electricity", "salary", "supplier", "transport", "maintenance", "other"]


class ExpenseCreate(BaseModel):
    amount: float
    expense_type: str
    description: Optional[str] = None
    date: Optional[str] = None


@router.post("/")
def add_expense(
    req: ExpenseCreate,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    expense_date = datetime.utcnow()
    if req.date:
        try:
            expense_date = datetime.fromisoformat(req.date)
        except ValueError:
            pass

    expense = models.Expense(
        owner_id=owner.id,
        amount=req.amount,
        expense_type=req.expense_type,
        description=req.description,
        date=expense_date,
    )
    db.add(expense)
    db.commit()
    return {"message": "Expense recorded", "id": expense.id}


@router.get("/")
def get_expenses(
    days: int = 30,
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    since = datetime.utcnow() - timedelta(days=days)
    expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == owner.id,
        models.Expense.date >= since
    ).order_by(models.Expense.date.desc()).all()

    by_type = {}
    for e in expenses:
        if e.expense_type not in by_type:
            by_type[e.expense_type] = 0
        by_type[e.expense_type] += e.amount

    return {
        "expenses": [
            {"id": e.id, "amount": e.amount, "type": e.expense_type,
             "description": e.description, "date": e.date}
            for e in expenses
        ],
        "total": round(sum(e.amount for e in expenses), 2),
        "by_type": by_type,
    }


@router.get("/monthly-fixed")
def get_monthly_fixed_costs(
    db: Session = Depends(get_db),
    owner: models.Owner = Depends(auth.get_current_owner),
):
    since = datetime.utcnow() - timedelta(days=30)
    expenses = db.query(models.Expense).filter(
        models.Expense.owner_id == owner.id,
        models.Expense.date >= since
    ).all()
    return {"total_monthly_expenses": round(sum(e.amount for e in expenses), 2)}
