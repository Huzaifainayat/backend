from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import RegistrationRequest, User
from models import RegistrationRequestCreate, RegistrationRequestResponse
from auth_utils import get_current_user

router = APIRouter(prefix="/registration-requests", tags=["registration-requests"])

@router.post("/", response_model=RegistrationRequestResponse)
def create_registration_request(
    request: RegistrationRequestCreate,
    db: Session = Depends(get_db)
):
    """Create a new registration request (public endpoint)"""
    # Check if email already exists
    existing_request = db.query(RegistrationRequest).filter(
        RegistrationRequest.email == request.email
    ).first()
    
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration request with this email already exists"
        )
    
    db_request = RegistrationRequest(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.get("/", response_model=List[RegistrationRequestResponse])
def get_registration_requests(
    status_filter: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all registration requests (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view registration requests"
        )
    
    query = db.query(RegistrationRequest)
    if status_filter:
        query = query.filter(RegistrationRequest.status == status_filter)
    
    return query.order_by(RegistrationRequest.created_at.desc()).all()

@router.get("/{request_id}", response_model=RegistrationRequestResponse)
def get_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific registration request (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view registration requests"
        )
    
    request = db.query(RegistrationRequest).filter(
        RegistrationRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration request not found"
        )
    
    return request

@router.put("/{request_id}/approve")
def approve_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve a registration request and create user account (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve registration requests"
        )
    
    request = db.query(RegistrationRequest).filter(
        RegistrationRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration request not found"
        )
    
    if request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request has already been processed"
        )
    
    # Create user account
    from auth_utils import get_password_hash
    
    # Generate username from email
    username = request.email.split('@')[0]
    counter = 1
    original_username = username
    
    # Ensure unique username
    while db.query(User).filter(User.username == username).first():
        username = f"{original_username}{counter}"
        counter += 1
    
    # Default password (should be changed on first login)
    default_password = "student123"
    
    new_user = User(
        username=username,
        email=request.email,
        password_hash=get_password_hash(default_password),
        name=f"{request.first_name} {request.last_name}",
        role="student"  # Default role for registration requests
    )
    
    db.add(new_user)
    request.status = "approved"
    db.commit()
    
    return {
        "message": "Registration request approved and user account created",
        "username": username,
        "default_password": default_password
    }

@router.put("/{request_id}/reject")
def reject_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a registration request (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reject registration requests"
        )
    
    request = db.query(RegistrationRequest).filter(
        RegistrationRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration request not found"
        )
    
    if request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request has already been processed"
        )
    
    request.status = "rejected"
    db.commit()
    
    return {"message": "Registration request rejected"}

@router.delete("/{request_id}")
def delete_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a registration request (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete registration requests"
        )
    
    request = db.query(RegistrationRequest).filter(
        RegistrationRequest.id == request_id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration request not found"
        )
    
    db.delete(request)
    db.commit()
    
    return {"message": "Registration request deleted successfully"}
