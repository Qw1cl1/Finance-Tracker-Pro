from celery import Task
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.v1.models.models import RecurringPayment, Transaction, Frequency
from celery_worker.celery_app import celery_app

# Database setup for Celery worker
DATABASE_URL = "postgresql://finance_user:finance_password@postgres:5432/finance_tracker"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_next_payment_date(current_date: datetime, frequency: Frequency) -> datetime:
    """Calculate the next payment date based on frequency."""
    if frequency == Frequency.DAILY:
        return current_date + timedelta(days=1)
    elif frequency == Frequency.WEEKLY:
        return current_date + timedelta(weeks=1)
    elif frequency == Frequency.MONTHLY:
        # Handle month overflow
        if current_date.month == 12:
            return current_date.replace(year=current_date.year + 1, month=1)
        else:
            try:
                return current_date.replace(month=current_date.month + 1)
            except ValueError:
                # Handle edge cases like Jan 31 -> Feb 28
                next_month = current_date.replace(month=current_date.month + 1, day=1)
                return next_month - timedelta(days=1)
    elif frequency == Frequency.YEARLY:
        return current_date.replace(year=current_date.year + 1)
    
    return current_date + timedelta(days=1)


@celery_app.task(bind=True, max_retries=3)
def process_recurring_payments(self) -> dict:
    """Process all due recurring payments and create transactions."""
    db = SessionLocal()
    results = {
        'processed': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        now = datetime.utcnow()
        
        # Get all active recurring payments that are due
        recurring_payments = db.query(RecurringPayment).filter(
            RecurringPayment.is_active == True,
            RecurringPayment.next_payment_date <= now
        ).all()
        
        for payment in recurring_payments:
            try:
                # Create a new transaction for this recurring payment
                transaction = Transaction(
                    title=payment.title,
                    amount=payment.amount,
                    date=now,
                    transaction_type='expense',
                    category_id=payment.category_id,
                    user_id=payment.user_id,
                    is_recurring=True,
                    recurring_payment_id=payment.id
                )
                
                db.add(transaction)
                
                # Update recurring payment
                payment.last_payment_date = now
                payment.next_payment_date = get_next_payment_date(
                    payment.next_payment_date,
                    payment.frequency
                )
                
                results['processed'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Payment {payment.id}: {str(e)}")
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60)
    
    finally:
        db.close()
    
    return results


@celery_app.task
def send_budget_alerts() -> dict:
    """Send alerts for budgets that are close to being exceeded."""
    # Placeholder for future implementation
    return {'status': 'completed'}
