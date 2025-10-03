from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# User models
class UserBase(BaseModel):
    username: str
    email: EmailStr
    name: str
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Assignment models
class AssignmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    subject: str
    class_name: str
    due_date: datetime

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentResponse(AssignmentBase):
    id: int
    created_by_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Assignment Submission models
class AssignmentSubmissionBase(BaseModel):
    content: str

class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    assignment_id: int

class AssignmentSubmissionResponse(AssignmentSubmissionBase):
    id: int
    assignment_id: int
    student_id: int
    submitted_at: datetime
    grade: Optional[str] = None
    feedback: Optional[str] = None
    
    class Config:
        from_attributes = True

class AssignmentSubmissionGrade(BaseModel):
    grade: str
    feedback: Optional[str] = None

# Message models
class MessageBase(BaseModel):
    subject: str
    content: str

class MessageCreate(MessageBase):
    receiver_id: int

class MessageResponse(MessageBase):
    id: int
    sender_id: int
    receiver_id: int
    sent_at: datetime
    is_read: bool
    
    class Config:
        from_attributes = True

# Registration Request models
class RegistrationRequestBase(BaseModel):
    username: str
    email: EmailStr
    name: str
    role: str

class RegistrationRequestCreate(RegistrationRequestBase):
    pass

class RegistrationRequestResponse(RegistrationRequestBase):
    id: int
    status: str
    requested_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class RegistrationRequestUpdate(BaseModel):
    status: str  # approved, rejected
