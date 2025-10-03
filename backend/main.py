from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import engine, Base, SessionLocal
from routers import auth, students, teachers, attendance, assignments, messages, registration_requests
from schemas import User
from auth_utils import get_password_hash
import uvicorn

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="School Management System API",
    description="Backend API for School Management System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React app URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(teachers.router, prefix="/api/teachers", tags=["teachers"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["attendance"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["assignments"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(registration_requests.router, prefix="/api/registration-requests", tags=["registration-requests"])

# Seed default users on startup (admin, teacher1, parent1, student1)
@app.on_event("startup")
def seed_default_users():
    db = SessionLocal()
    try:
        def ensure_user(username, email, password, name, role):
            if not db.query(User).filter(User.username == username).first():
                db.add(User(
                    username=username,
                    email=email,
                    password_hash=get_password_hash(password),
                    name=name,
                    role=role,
                ))
                db.commit()
        ensure_user("admin", "admin@school.com", "admin123", "Administrator", "admin")
        ensure_user("teacher1", "teacher1@school.com", "teacher123", "Teacher One", "teacher")
        ensure_user("parent1", "parent1@school.com", "parent123", "Parent One", "parent")
        ensure_user("student1", "student1@school.com", "student123", "Student One", "student")
        print("Ensured demo users exist: admin, teacher1, parent1, student1")
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "School Management System API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)