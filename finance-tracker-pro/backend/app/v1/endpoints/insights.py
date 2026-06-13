from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from sqlalchemy import func

from app.core.database import get_db
from app.v1.models.models import Transaction, Category, Budget, TransactionType
from app.v1.schemas.schemas import Insight
from app.v1.endpoints.auth import get_current_user
from app.v1.models.models import User

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/", response_model=List[Insight])
def get_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered financial insights based on user data."""
    insights = []
    now = datetime.utcnow()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = current_month_start
    last_month_start = (last_month_end - timedelta(days=1)).replace(day=1)
    
    # Get current and previous month expenses
    current_month_expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.date >= current_month_start
    ).scalar() or 0
    
    previous_month_expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.date >= last_month_start,
        Transaction.date < last_month_end
    ).scalar() or 0
    
    # Insight 1: Expense trend comparison
    if previous_month_expenses > 0:
        change_percent = ((current_month_expenses - previous_month_expenses) / previous_month_expenses) * 100
        if change_percent > 10:
            insights.append(Insight(
                message=f"Расходы выросли на {abs(change_percent):.0f}% по сравнению с прошлым месяцем.",
                type="warning",
                category="Общие расходы"
            ))
        elif change_percent < -10:
            insights.append(Insight(
                message=f"Расходы снизились на {abs(change_percent):.0f}% по сравнению с прошлым месяцем.",
                type="success",
                category="Общие расходы"
            ))
    
    # Insight 2: Category-specific analysis
    category_expenses_current = db.query(
        Category.id,
        Category.name,
        func.sum(Transaction.amount).label('total')
    ).join(
        Transaction,
        Transaction.category_id == Category.id
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.date >= current_month_start
    ).group_by(Category.id, Category.name).all()
    
    category_expenses_previous = db.query(
        Category.id,
        func.sum(Transaction.amount).label('total')
    ).join(
        Transaction,
        Transaction.category_id == Category.id
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.date >= last_month_start,
        Transaction.date < last_month_end
    ).group_by(Category.id).dict()
    
    for cat in category_expenses_current:
        prev_total = category_expenses_previous.get(cat.id, {}).get('total', 0)
        if prev_total > 0:
            cat_change = ((cat.total - prev_total) / prev_total) * 100
            if cat_change > 20:
                insights.append(Insight(
                    message=f"Расходы на категорию '{cat.name}' выросли на {abs(cat_change):.0f}%.",
                    type="warning",
                    category=cat.name
                ))
    
    # Insight 3: Budget warnings
    budgets = db.query(Budget, Category).join(
        Category, Budget.category_id == Category.id
    ).filter(Budget.user_id == current_user.id).all()
    
    days_in_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - now.replace(day=1)
    days_remaining = days_in_month.days
    days_passed = now.day
    
    for budget, category in budgets:
        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.category_id == budget.category_id,
            Transaction.date >= current_month_start
        ).scalar() or 0
        
        remaining_budget = budget.limit_amount - spent
        daily_average = spent / days_passed if days_passed > 0 else 0
        projected_total = daily_average * (days_passed + days_remaining)
        
        if spent > budget.limit_amount:
            insights.append(Insight(
                message=f"Бюджет '{category.name}' превышен на {spent - budget.limit_amount:.0f} ₸.",
                type="warning",
                category=category.name
            ))
        elif projected_total > budget.limit_amount and remaining_budget > 0:
            days_until_exceeded = remaining_budget / daily_average if daily_average > 0 else 999
            if days_until_exceeded < days_remaining:
                insights.append(Insight(
                    message=f"Если текущая тенденция сохранится, бюджет '{category.name}' будет превышен через {int(days_until_exceeded)} дн.",
                    type="warning",
                    category=category.name
                ))
    
    # Insight 4: Savings rate
    current_month_income = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.INCOME,
        Transaction.date >= current_month_start
    ).scalar() or 0
    
    if current_month_income > 0:
        savings_rate = ((current_month_income - current_month_expenses) / current_month_income) * 100
        if savings_rate >= 20:
            insights.append(Insight(
                message=f"Отлично! Вы откладываете {savings_rate:.0f}% дохода в этом месяце.",
                type="success",
                category="Накопления"
            ))
        elif savings_rate < 10 and savings_rate >= 0:
            insights.append(Insight(
                message=f"Ваш уровень накоплений всего {savings_rate:.0f}%. Попробуйте откладывать больше.",
                type="info",
                category="Накопления"
            ))
        elif savings_rate < 0:
            insights.append(Insight(
                message=f"В этом месяце вы потратили больше, чем заработали ({abs(savings_rate):.0f}%).",
                type="warning",
                category="Накопления"
            ))
    
    # Default insight if no specific findings
    if not insights:
        insights.append(Insight(
            message="Ваши финансы в стабильном состоянии. Продолжайте в том же духе!",
            type="success",
            category="Общее"
        ))
    
    return insights
