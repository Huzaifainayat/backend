from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import User, Assignment, AssignmentSubmission
from models import AssignmentResponse, AssignmentSubmissionCreate, AssignmentSubmissionResponse
from auth_utils import get_current_user

router = APIRouter()

@router.get("/assignments", response_model=List[AssignmentResponse])
def get_student_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assignments for the current student"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    assignments = db.query(Assignment).all()
    return assignments

@router.post("/assignments/{assignment_id}/submit", response_model=AssignmentSubmissionResponse)
def submit_assignment(
    assignment_id: int,
    submission: AssignmentSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit an assignment"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit assignments"
        )
    
    # Check if assignment exists
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if student has already submitted
    existing_submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_id == current_user.id
    ).first()
    
    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment already submitted"
        )
    
    db_submission = AssignmentSubmission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        content=submission.content
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

@router.get("/submissions", response_model=List[AssignmentSubmissionResponse])
def get_student_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all submissions for the current student"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.student_id == current_user.id
    ).all()
    return submissions
