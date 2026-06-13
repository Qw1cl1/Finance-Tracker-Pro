from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.v1.models.models import RecurringPayment, Frequency
from app.v1.schemas.schemas import (
    RecurringPaymentCreate,
    RecurringPaymentUpdate,
    RecurringPaymentResponse
)
from app.v1.endpoints.auth import get_current_user
from app.v1.models.models import User

router = APIRouter(prefix="/recurring-payments", tags=["Recurring Payments"])


@router.get("/", response_model=List[RecurringPaymentResponse])
def get_recurring_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all recurring payments for the current user."""
    recurring_payments = db.query(RecurringPayment).filter(
        RecurringPayment.user_id == current_user.id
    ).all()
    
    return recurring_payments


@router.get("/{payment_id}", response_model=RecurringPaymentResponse)
def get_recurring_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific recurring payment by ID."""
    payment = db.query(RecurringPayment).filter(
        RecurringPayment.id == payment_id,
        RecurringPayment.user_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring payment not found"
        )
    
    return payment


@router.post("/", response_model=RecurringPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_payment(
    payment_data: RecurringPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new recurring payment."""
    new_payment = RecurringPayment(
        **payment_data.model_dump(),
        user_id=current_user.id
    )
    
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    
    return new_payment


@router.put("/{payment_id}", response_model=RecurringPaymentResponse)
def update_recurring_payment(
    payment_id: int,
    payment_data: RecurringPaymentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing recurring payment."""
    payment = db.query(RecurringPayment).filter(
        RecurringPayment.id == payment_id,
        RecurringPayment.user_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring payment not found"
        )
    
    # Update fields
    update_data = payment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)
    
    db.commit()
    db.refresh(payment)
    
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a recurring payment."""
    payment = db.query(RecurringPayment).filter(
        RecurringPayment.id == payment_id,
        RecurringPayment.user_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring payment not found"
        )
    
    db.delete(payment)
    db.commit()
    
    return None
