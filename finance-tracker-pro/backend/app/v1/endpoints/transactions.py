from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.v1.models.models import Transaction, Category, TransactionType
from app.v1.schemas.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse
)
from app.v1.endpoints.auth import get_current_user
from app.v1.models.models import User

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 50,
    transaction_type: Optional[TransactionType] = None,
    category_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all transactions for the current user with filtering."""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    # Apply filters
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    
    if category_id:
        query = query.filter(
            (Transaction.category_id == category_id) | 
            (Transaction.subcategory_id == category_id)
        )
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    if search:
        query = query.filter(Transaction.title.ilike(f"%{search}%"))
    
    # Order by date descending
    query = query.order_by(Transaction.date.desc())
    
    transactions = query.offset(skip).limit(limit).all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific transaction by ID."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new transaction."""
    # Validate category if provided
    if transaction_data.category_id:
        category = db.query(Category).filter(
            Category.id == transaction_data.category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found"
            )
    
    # Set default date if not provided
    if not transaction_data.date:
        transaction_data.date = datetime.utcnow()
    
    new_transaction = Transaction(
        **transaction_data.model_dump(),
        user_id=current_user.id
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return new_transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing transaction."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Update fields
    update_data = transaction_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a transaction."""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    db.delete(transaction)
    db.commit()
    
    return None
