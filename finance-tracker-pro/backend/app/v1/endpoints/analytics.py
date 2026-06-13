from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from sqlalchemy import func, extract

from app.core.database import get_db
from app.v1.models.models import Transaction, Category, TransactionType
from app.v1.schemas.schemas import (
    AnalyticsResponse,
    CategoryAnalytics,
    MonthlyTrend
)
from app.v1.endpoints.auth import get_current_user
from app.v1.models.models import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/", response_model=AnalyticsResponse)
def get_analytics(
    months: int = 6,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics for the current user using SQL aggregations."""
    
    now = datetime.utcnow()
    start_date = now - timedelta(days=months * 30)
    
    # Get expenses by category using CTE-like query
    category_expenses = db.query(
        Category.id,
        Category.name,
        Category.color,
        func.sum(Transaction.amount).label('total_amount'),
        func.count(Transaction.id).label('transaction_count')
    ).join(
        Transaction,
        Transaction.category_id == Category.id
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.date >= start_date
    ).group_by(
        Category.id,
        Category.name,
        Category.color
    ).order_by(
        func.sum(Transaction.amount).desc()
    ).all()
    
    # Calculate total expenses for percentage
    total_expenses = sum(cat.total_amount for cat in category_expenses) or 1
    
    categories = [
        CategoryAnalytics(
            category_id=cat.id,
            category_name=cat.name,
            total_amount=float(cat.total_amount),
            transaction_count=cat.transaction_count,
            percentage=round((cat.total_amount / total_expenses) * 100, 2),
            color=cat.color
        )
        for cat in category_expenses
    ]
    
    # Get monthly trends using window functions approach
    monthly_data = db.query(
        extract('year', Transaction.date).label('year'),
        extract('month', Transaction.date).label('month'),
        func.sum(
            func.case(
                (Transaction.transaction_type == TransactionType.INCOME, Transaction.amount),
                else_=0
            )
        ).label('income'),
        func.sum(
            func.case(
                (Transaction.transaction_type == TransactionType.EXPENSE, Transaction.amount),
                else_=0
            )
        ).label('expense')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date
    ).group_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).order_by(
        extract('year', Transaction.date),
        extract('month', Transaction.date)
    ).all()
    
    monthly_trends = [
        MonthlyTrend(
            month=f"{int(row.year)}-{int(row.month):02d}",
            income=float(row.income),
            expense=float(row.expense),
            net=float(row.income - row.expense)
        )
        for row in monthly_data
    ]
    
    # Top 5 categories
    top_categories = categories[:5]
    
    # Average daily expense
    days_count = (now - start_date).days or 1
    average_daily_expense = total_expenses / days_count
    
    # Period comparison (current vs previous period)
    previous_start = start_date - timedelta(days=months * 30)
    
    current_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.date >= start_date
    ).scalar() or 0
    
    current_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.date >= start_date
    ).scalar() or 0
    
    previous_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.date >= previous_start,
        Transaction.date < start_date
    ).scalar() or 0
    
    previous_expense = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.date >= previous_start,
        Transaction.date < start_date
    ).scalar() or 0
    
    comparison = {
        "income_change": round(((current_income - previous_income) / previous_income * 100) if previous_income else 0, 2),
        "expense_change": round(((current_expense - previous_expense) / previous_expense * 100) if previous_expense else 0, 2),
        "current_income": float(current_income),
        "previous_income": float(previous_income),
        "current_expense": float(current_expense),
        "previous_expense": float(previous_expense)
    }
    
    return AnalyticsResponse(
        categories=categories,
        monthly_trends=monthly_trends,
        top_categories=top_categories,
        average_daily_expense=round(average_daily_expense, 2),
        comparison=comparison
    )
