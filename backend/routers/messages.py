from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from schemas import Message, User
from models import MessageCreate, MessageResponse
from auth_utils import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=MessageResponse)
def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message to another user"""
    # Check if recipient exists
    recipient = db.query(User).filter(User.id == message.to_user_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    db_message = Message(
        **message.dict(),
        from_user_id=current_user.id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@router.get("/", response_model=List[MessageResponse])
def get_messages(
    message_type: Optional[str] = None,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages for current user"""
    query = db.query(Message).filter(Message.to_user_id == current_user.id)
    
    if message_type:
        query = query.filter(Message.message_type == message_type)
    
    if unread_only:
        query = query.filter(Message.read == False)
    
    return query.order_by(Message.created_at.desc()).all()

@router.get("/sent", response_model=List[MessageResponse])
def get_sent_messages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages sent by current user"""
    return db.query(Message).filter(
        Message.from_user_id == current_user.id
    ).order_by(Message.created_at.desc()).all()

@router.get("/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific message"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if user is sender or recipient
    if message.from_user_id != current_user.id and message.to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this message"
        )
    
    return message

@router.put("/{message_id}/read")
def mark_message_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a message as read"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Only recipient can mark as read
    if message.to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark your own messages as read"
        )
    
    message.read = True
    db.commit()
    return {"message": "Message marked as read"}

@router.get("/unread/count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread messages"""
    count = db.query(Message).filter(
        Message.to_user_id == current_user.id,
        Message.read == False
    ).count()
    return {"unread_count": count}

@router.get("/teachers")
def get_teachers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of teachers for messaging"""
    if current_user.role not in ["student", "parent", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    teachers = db.query(User).filter(User.role == "teacher").all()
    return [{"id": t.id, "name": t.name, "username": t.username} for t in teachers]

@router.post("/send-to-teacher")
def send_message_to_teacher(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send message to any teacher (for students and parents)"""
    if current_user.role not in ["student", "parent"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and parents can send messages to teachers"
        )
    
    # Find a teacher to send to (or use the specified to_user_id)
    if message.to_user_id:
        teacher = db.query(User).filter(
            User.id == message.to_user_id,
            User.role == "teacher"
        ).first()
    else:
        # Send to first available teacher
        teacher = db.query(User).filter(User.role == "teacher").first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No teachers found"
        )
    
    db_message = Message(
        subject=message.subject,
        content=message.content,
        message_type=message.message_type or 'message',
        from_user_id=current_user.id,
        to_user_id=teacher.id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message
