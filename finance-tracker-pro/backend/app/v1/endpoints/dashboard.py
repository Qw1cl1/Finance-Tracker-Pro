from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

from app.core.database import get_db
from app.v1.models.models import Transaction, TransactionType
from app.v1.schemas.schemas import DashboardSummary, TransactionResponse
from app.v1.endpoints.auth import get_current_user
from app.v1.models.models import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard summary with balance, income, expenses, and recent transactions."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate total balance (all time income - all time expenses)
    total_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.INCOME
    ).scalar() or 0
    
    total_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE
    ).scalar() or 0
    
    total_balance = float(total_income - total_expense)
    
    # Calculate monthly income and expenses
    monthly_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.date >= month_start
    ).scalar() or 0
    
    monthly_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.date >= month_start
    ).scalar() or 0
    
    # Savings (current month net)
    savings = float(monthly_income - monthly_expense)
    
    # Get recent transactions (last 10)
    recent_transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).limit(10).all()
    
    return DashboardSummary(
        total_balance=total_balance,
        monthly_income=float(monthly_income),
        monthly_expense=float(monthly_expense),
        savings=savings,
        recent_transactions=recent_transactions
    )
