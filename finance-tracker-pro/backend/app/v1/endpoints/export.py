from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from sqlalchemy import func
import io
import csv
from fastapi.responses import StreamingResponse

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from app.core.database import get_db
from app.v1.models.models import Transaction, TransactionType
from app.v1.schemas.schemas import TransactionResponse
from app.v1.endpoints.auth import get_current_user
from app.v1.models.models import User

router = APIRouter(prefix="/export", tags=["Export/Import"])


@router.get("/csv")
def export_transactions_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export transactions to CSV format."""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Title', 'Amount', 'Date', 'Type', 
        'Category', 'Subcategory', 'Comment'
    ])
    
    # Write data
    for tx in transactions:
        writer.writerow([
            tx.id,
            tx.title,
            float(tx.amount),
            tx.date.strftime('%Y-%m-%d %H:%M:%S'),
            tx.transaction_type.value,
            tx.category.name if tx.category else '',
            tx.subcategory.name if tx.subcategory else '',
            tx.comment or ''
        ])
    
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=transactions.csv"
        }
    )


@router.get("/xlsx")
def export_transactions_xlsx(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export transactions to XLSX format."""
    if not PANDAS_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pandas is not available"
        )
    
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).all()
    
    # Prepare data for DataFrame
    data = []
    for tx in transactions:
        data.append({
            'ID': tx.id,
            'Title': tx.title,
            'Amount': float(tx.amount),
            'Date': tx.date.strftime('%Y-%m-%d %H:%M:%S'),
            'Type': tx.transaction_type.value,
            'Category': tx.category.name if tx.category else '',
            'Subcategory': tx.subcategory.name if tx.subcategory else '',
            'Comment': tx.comment or ''
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Transactions', index=False)
    
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=transactions.xlsx"
        }
    )


@router.post("/csv")
async def import_transactions_csv(
    file: bytes,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import transactions from CSV format."""
    try:
        # Decode CSV content
        content = file.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        
        imported_count = 0
        
        for row in reader:
            try:
                # Parse transaction type
                tx_type = TransactionType(row.get('Type', 'expense').lower())
                
                # Parse date
                date_str = row.get('Date', '')
                if date_str:
                    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                else:
                    date = datetime.utcnow()
                
                # Create transaction
                new_transaction = Transaction(
                    title=row.get('Title', 'Imported Transaction'),
                    amount=float(row.get('Amount', 0)),
                    date=date,
                    transaction_type=tx_type,
                    comment=row.get('Comment', ''),
                    user_id=current_user.id
                )
                
                db.add(new_transaction)
                imported_count += 1
                
            except Exception as e:
                continue  # Skip invalid rows
        
        db.commit()
        
        return {
            "message": f"Successfully imported {imported_count} transactions",
            "count": imported_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error importing CSV: {str(e)}"
        )


@router.post("/xlsx")
async def import_transactions_xlsx(
    file: bytes,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import transactions from XLSX format."""
    if not PANDAS_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pandas is not available"
        )
    
    try:
        # Read Excel file
        output = io.BytesIO(file)
        df = pd.read_excel(output)
        
        imported_count = 0
        
        for _, row in df.iterrows():
            try:
                # Parse transaction type
                tx_type_str = str(row.get('Type', 'expense')).lower()
                tx_type = TransactionType.INCOME if 'income' in tx_type_str else TransactionType.EXPENSE
                
                # Parse date
                date = row.get('Date')
                if isinstance(date, str):
                    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                elif not isinstance(date, datetime):
                    date = datetime.utcnow()
                
                # Create transaction
                new_transaction = Transaction(
                    title=str(row.get('Title', 'Imported Transaction')),
                    amount=float(row.get('Amount', 0)),
                    date=date,
                    transaction_type=tx_type,
                    comment=str(row.get('Comment', '')),
                    user_id=current_user.id
                )
                
                db.add(new_transaction)
                imported_count += 1
                
            except Exception as e:
                continue  # Skip invalid rows
        
        db.commit()
        
        return {
            "message": f"Successfully imported {imported_count} transactions",
            "count": imported_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error importing XLSX: {str(e)}"
        )
