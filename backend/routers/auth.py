from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from schemas import User, RegistrationRequest
from models import UserLogin, Token, UserResponse, RegistrationRequestCreate, RegistrationRequestResponse, RegistrationRequestUpdate
from auth_utils import verify_password, create_access_token, get_password_hash, get_current_user
from typing import List
from datetime import datetime

router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all users"
        )
    
    users = db.query(User).all()
    return users

@router.post("/register-request", response_model=RegistrationRequestResponse)
def create_registration_request(request: RegistrationRequestCreate, db: Session = Depends(get_db)):
    """Create a new registration request"""
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Check if there's already a pending request
    existing_request = db.query(RegistrationRequest).filter(
        (RegistrationRequest.username == request.username) | 
        (RegistrationRequest.email == request.email)
    ).filter(RegistrationRequest.status == "pending").first()
    
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration request already pending"
        )
    
    db_request = RegistrationRequest(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.get("/register-requests", response_model=List[RegistrationRequestResponse])
def get_registration_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all registration requests (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view registration requests"
        )
    
    requests = db.query(RegistrationRequest).all()
    return requests

@router.put("/register-requests/{request_id}", response_model=RegistrationRequestResponse)
def process_registration_request(
    request_id: int,
    request_update: RegistrationRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process a registration request (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can process registration requests"
        )
    
    db_request = db.query(RegistrationRequest).filter(RegistrationRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration request not found"
        )
    
    if db_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request has already been processed"
        )
    
    db_request.status = request_update.status
    db_request.processed_at = datetime.utcnow()
    
    # If approved, create the user account
    if request_update.status == "approved":
        # Generate a default password (in production, this should be sent via email)
        default_password = f"{db_request.username}123"
        
        new_user = User(
            username=db_request.username,
            email=db_request.email,
            name=db_request.name,
            role=db_request.role,
            password_hash=get_password_hash(default_password)
        )
        db.add(new_user)
    
    db.commit()
    db.refresh(db_request)
    return db_request
