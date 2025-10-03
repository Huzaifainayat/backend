from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import User, Assignment, AssignmentSubmission
from models import AssignmentCreate, AssignmentResponse, AssignmentSubmissionResponse, AssignmentSubmissionGrade
from auth_utils import get_current_user

router = APIRouter()

@router.post("/assignments", response_model=AssignmentResponse)
def create_assignment(
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new assignment (teachers only)"""
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create assignments"
        )
    
    db_assignment = Assignment(
        **assignment.dict(),
        created_by_id=current_user.id
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@router.get("/assignments", response_model=List[AssignmentResponse])
def get_teacher_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assignments created by the current teacher"""
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can access this endpoint"
        )
    
    if current_user.role == "admin":
        assignments = db.query(Assignment).all()
    else:
        assignments = db.query(Assignment).filter(
            Assignment.created_by_id == current_user.id
        ).all()
    
    return assignments

@router.get("/assignments/{assignment_id}/submissions", response_model=List[AssignmentSubmissionResponse])
def get_assignment_submissions(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all submissions for a specific assignment"""
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can view submissions"
        )
    
    # Check if assignment exists and belongs to teacher (unless admin)
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    if current_user.role == "teacher" and assignment.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view submissions for your own assignments"
        )
    
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id
    ).all()
    return submissions

@router.put("/submissions/{submission_id}/grade", response_model=AssignmentSubmissionResponse)
def grade_submission(
    submission_id: int,
    grade_data: AssignmentSubmissionGrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Grade a student's submission"""
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can grade submissions"
        )
    
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.id == submission_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Check if teacher owns the assignment (unless admin)
    if current_user.role == "teacher":
        assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
        if assignment.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only grade submissions for your own assignments"
            )
    
    submission.grade = grade_data.grade
    submission.feedback = grade_data.feedback
    db.commit()
    db.refresh(submission)
    return submission
