# backend/app/api/v1/auth.py
"""Enhanced Authentication API endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.config.database import get_db
from app.services.auth_service import AuthService
from studysprint_db.schemas.user import (
    UserCreate, UserUpdate, UserResponse, TokenResponse, 
    UserPreferencesUpdate, UserPreferencesResponse, UserSessionResponse
)
from studysprint_db.models.user import User, UserPreferences

router = APIRouter()

# Additional schemas for auth endpoints
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutAllRequest(BaseModel):
    confirm: bool = True

def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent"""
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "Unknown")
    return ip, user_agent

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to get current authenticated user"""
    # Extract token from Authorization header
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    return AuthService.get_current_user(db, token)

# Authentication endpoints
@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    ip_address, user_agent = get_client_info(request)
    
    try:
        auth_data = AuthService.register_user(
            db=db,
            user_create=user_create,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "message": "User registered successfully",
            "user": UserResponse.from_orm(auth_data["user"]),
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"],
            "token_type": auth_data["token_type"],
            "expires_in": auth_data["expires_in"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens"""
    ip_address, user_agent = get_client_info(request)
    
    try:
        auth_data = AuthService.authenticate_user(
            db=db,
            email=form_data.username,  # OAuth2 uses 'username' field for email
            password=form_data.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "message": "Login successful",
            "user": UserResponse.from_orm(auth_data["user"]),
            "access_token": auth_data["access_token"],
            "refresh_token": auth_data["refresh_token"],
            "token_type": auth_data["token_type"],
            "expires_in": auth_data["expires_in"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        token_data = AuthService.refresh_token(db, refresh_request.refresh_token)
        return TokenResponse(**token_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """Logout current session"""
    try:
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            success = AuthService.logout_user(db, token)
            
            if success:
                return {"message": "Logged out successfully"}
            else:
                return {"message": "Session not found or already logged out"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid session found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.post("/logout-all")
async def logout_all_sessions(
    logout_request: LogoutAllRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout from all devices"""
    if not logout_request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm logout from all devices"
        )
    
    try:
        count = AuthService.logout_all_sessions(db, str(current_user.id))
        return {
            "message": f"Logged out from {count} devices successfully",
            "sessions_invalidated": count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout all failed: {str(e)}"
        )

# User profile endpoints
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    try:
        updated_user = AuthService.update_user_profile(
            db=db,
            user_id=str(current_user.id),
            user_update=user_update
        )
        return UserResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    password_request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        success = AuthService.change_password(
            db=db,
            user_id=str(current_user.id),
            current_password=password_request.current_password,
            new_password=password_request.new_password
        )
        
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

# User preferences endpoints
@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user preferences"""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences if they don't exist
        preferences = UserPreferences(user_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return UserPreferencesResponse.from_orm(preferences)

@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        preferences = UserPreferences(user_id=current_user.id)
        db.add(preferences)
    
    # Update preferences
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    db.commit()
    db.refresh(preferences)
    
    return UserPreferencesResponse.from_orm(preferences)

# Session management endpoints
@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active sessions for current user"""
    try:
        sessions = AuthService.get_user_sessions(db, str(current_user.id))
        return [UserSessionResponse.from_orm(session) for session in sessions]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )

# Health check
@router.get("/health")
async def auth_health_check():
    """Health check for authentication service"""
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "2.0.0",
        "features": [
            "registration",
            "login",
            "jwt_tokens",
            "refresh_tokens",
            "session_management",
            "user_preferences",
            "password_change",
            "multi_device_logout"
        ]
    }