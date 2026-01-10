from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.business import Business
from ..services.auth import get_current_user

router = APIRouter(prefix="/business", tags=["Business"])


# ============== SCHEMAS ==============

class BusinessCreate(BaseModel):
    name: str
    business_type: Optional[str] = None  # e.g., "salon", "restaurant", "fitness"
    address: Optional[str] = None
    phone: Optional[str] = None


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class BusinessResponse(BaseModel):
    id: int
    name: str
    business_type: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== ENDPOINTS ==============

@router.post("/", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
def create_business(
    business_data: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new business for the authenticated user."""
    new_business = Business(
        name=business_data.name,
        business_type=business_data.business_type,
        address=business_data.address,
        phone=business_data.phone,
        owner_id=current_user.id
    )
    
    db.add(new_business)
    db.commit()
    db.refresh(new_business)
    
    return new_business


@router.get("/", response_model=list[BusinessResponse])
def get_my_businesses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all businesses owned by the authenticated user."""
    businesses = db.query(Business).filter(Business.owner_id == current_user.id).all()
    return businesses


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific business by ID."""
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    return business


@router.put("/{business_id}", response_model=BusinessResponse)
def update_business(
    business_id: int,
    business_data: BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a business."""
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    # Update only provided fields
    update_data = business_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(business, field, value)
    
    db.commit()
    db.refresh(business)
    
    return business


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business(
    business_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a business."""
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.owner_id == current_user.id
    ).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    db.delete(business)
    db.commit()
    
    return None