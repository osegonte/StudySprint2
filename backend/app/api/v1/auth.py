"""Basic Authentication API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.config.database import get_db

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str = None

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str = None

@router.post("/register", response_model=dict)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    return {
        "message": "User registered successfully",
        "user": {
            "id": "123",
            "email": user_create.email,
            "username": user_create.username,
            "full_name": user_create.full_name
        },
        "access_token": "dummy-token",
        "token_type": "bearer"
    }

@router.post("/login", response_model=dict)
async def login(db: Session = Depends(get_db)):
    """Login user"""
    return {
        "message": "Login successful",
        "access_token": "dummy-token",
        "token_type": "bearer"
    }

@router.get("/me", response_model=dict)
async def get_current_user(db: Session = Depends(get_db)):
    """Get current user"""
    return {
        "id": "123",
        "email": "test@example.com",
        "username": "testuser"
    }

@router.get("/health")
async def auth_health_check():
    """Health check for authentication service"""
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "2.0.0"
    }
