from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import csv
import io

from ..database import get_db
from ..models.user import User
from ..models.business import Business
from ..models.transaction import Transaction
from ..services.auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ============== SCHEMAS ==============

class TransactionCreate(BaseModel):
    amount: float
    customer_id: Optional[str] = None
    transaction_date: datetime
    category: Optional[str] = None
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    business_id: int
    amount: float
    customer_id: Optional[str]
    transaction_date: datetime
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============== HELPER ==============

def verify_business_ownership(db: Session, business_id: int, user: User) -> Business:
    """Verify the user owns this business."""
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.owner_id == user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    return business


# ============== ENDPOINTS ==============

@router.post("/upload/{business_id}")
async def upload_csv(
    business_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload transactions via CSV file.
    
    Expected CSV columns: amount, date, customer_id (optional), category (optional)
    """
    verify_business_ownership(db, business_id, current_user)
    
    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode('utf-8')))
    
    transactions = []
    for row in reader:
        tx = Transaction(
            business_id=business_id,
            amount=float(row['amount']),
            customer_id=row.get('customer_id'),
            transaction_date=datetime.fromisoformat(row['date']),
            category=row.get('category')
        )
        transactions.append(tx)
    
    db.bulk_save_objects(transactions)
    db.commit()
    
    return {"imported": len(transactions)}


@router.post("/{business_id}", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    business_id: int,
    transaction_data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a single transaction manually."""
    verify_business_ownership(db, business_id, current_user)
    
    new_transaction = Transaction(
        business_id=business_id,
        amount=transaction_data.amount,
        customer_id=transaction_data.customer_id,
        transaction_date=transaction_data.transaction_date,
        category=transaction_data.category,
        description=transaction_data.description
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return new_transaction


@router.get("/{business_id}", response_model=list[TransactionResponse])
def get_transactions(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all transactions for a business."""
    verify_business_ownership(db, business_id, current_user)
    
    return db.query(Transaction).filter(
        Transaction.business_id == business_id
    ).order_by(Transaction.transaction_date.desc()).all()