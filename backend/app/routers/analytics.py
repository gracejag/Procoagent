from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date

from ..database import get_db
from ..models.user import User
from ..models.business import Business
from ..services.auth import get_current_user
from ..services.analytics import get_daily_revenue, get_revenue_summary

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ============== SCHEMAS ==============

class DailyRevenueResponse(BaseModel):
    date: date
    revenue: float
    transaction_count: int


class RevenueSummaryResponse(BaseModel):
    today: float
    this_week: float
    this_month: float


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

@router.get("/{business_id}/daily")
def get_daily_analytics(
    business_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily revenue for the past N days."""
    verify_business_ownership(db, business_id, current_user)
    
    results = get_daily_revenue(db, business_id, days)
    
    return [
        {
            "date": row.date,
            "revenue": row.revenue or 0.0,
            "transaction_count": row.transaction_count
        }
        for row in results
    ]


@router.get("/{business_id}/summary", response_model=RevenueSummaryResponse)
def get_summary_analytics(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get revenue summary: today, this week, this month."""
    verify_business_ownership(db, business_id, current_user)
    
    return get_revenue_summary(db, business_id)