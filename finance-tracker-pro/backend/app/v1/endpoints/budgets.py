from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from sqlalchemy import func

from app.core.database import get_db
from app.v1.models.models import Budget, Transaction, Category, TransactionType
from app.v1.schemas.schemas import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse
)
from app.v1.endpoints.auth import get_current_user
from app.v1.models.models import User

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def get_period_dates(period: str):
    """Get start and end dates for a budget period."""
    now = datetime.utcnow()
    
    if period == "daily":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
    elif period == "weekly":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(weeks=1)
    elif period == "yearly":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(year=now.year + 1)
    else:  # monthly (default)
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_date = start_date.replace(year=now.year + 1, month=1)
        else:
            end_date = start_date.replace(month=now.month + 1)
    
    return start_date, end_date


@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all budgets for the current user with spent amounts."""
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    
    budget_responses = []
    for budget in budgets:
        start_date, end_date = get_period_dates(budget.period)
        
        # Calculate spent amount for this budget's category in the current period
        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.category_id == budget.category_id,
            Transaction.date >= start_date,
            Transaction.date < end_date
        ).scalar() or 0
        
        budget_dict = {
            "id": budget.id,
            "category_id": budget.category_id,
            "limit_amount": float(budget.limit_amount),
            "period": budget.period,
            "user_id": budget.user_id,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "created_at": budget.created_at,
            "updated_at": budget.updated_at,
            "category": budget.category,
            "spent_amount": float(spent),
            "is_exceeded": spent > budget.limit_amount
        }
        
        budget_responses.append(BudgetResponse(**budget_dict))
    
    return budget_responses


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific budget by ID."""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Calculate spent amount
    start_date, end_date = get_period_dates(budget.period)
    spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.EXPENSE,
        Transaction.category_id == budget.category_id,
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).scalar() or 0
    
    budget_dict = {
        "id": budget.id,
        "category_id": budget.category_id,
        "limit_amount": float(budget.limit_amount),
        "period": budget.period,
        "user_id": budget.user_id,
        "start_date": budget.start_date,
        "end_date": budget.end_date,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
        "category": budget.category,
        "spent_amount": float(spent),
        "is_exceeded": spent > budget.limit_amount
    }
    
    return BudgetResponse(**budget_dict)


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new budget."""
    # Validate category
    category = db.query(Category).filter(
        Category.id == budget_data.category_id,
        Category.user_id == current_user.id
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found"
        )
    
    new_budget = Budget(
        **budget_data.model_dump(),
        user_id=current_user.id
    )
    
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    
    return new_budget


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing budget."""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Update fields
    update_data = budget_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)
    
    db.commit()
    db.refresh(budget)
    
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a budget."""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    db.delete(budget)
    db.commit()
    
    return None
