# backend/app/services/auth_service.py
"""Enhanced Authentication Service for StudySprint 2.0"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

from studysprint_db.models.user import User, UserSession, UserPreferences
from studysprint_db.schemas.user import UserCreate, UserUpdate, TokenResponse
from app.config.settings import settings

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class AuthService:
    """Complete authentication and session management service"""
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=30)  # Refresh tokens last 30 days
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # Unique token ID
        }
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise JWTError("Invalid token type")
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                raise JWTError("Token expired")
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def register_user(db: Session, user_create: UserCreate, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Register a new user with session creation"""
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_create.email) | (User.username == user_create.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_create.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create user
        hashed_password = AuthService.get_password_hash(user_create.password)
        
        db_user = User(
            email=user_create.email.lower(),
            username=user_create.username.lower(),
            hashed_password=hashed_password,
            full_name=user_create.full_name
        )
        
        db.add(db_user)
        db.flush()  # Get the user ID without committing
        
        # Create default preferences
        preferences = UserPreferences(user_id=db_user.id)
        db.add(preferences)
        
        # Create tokens and session
        access_token = AuthService.create_access_token(data={"sub": db_user.email, "user_id": str(db_user.id)})
        refresh_token = AuthService.create_refresh_token(db_user.id)
        
        # Create session record
        session = UserSession(
            user_id=db_user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(session)
        db.commit()
        db.refresh(db_user)
        
        return {
            "user": db_user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Authenticate user and create session"""
        
        # Find user by email
        user = db.query(User).filter(
            User.email == email.lower(),
            User.is_deleted == False,
            User.is_active == True
        ).first()
        
        if not user or not AuthService.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        access_token = AuthService.create_access_token(data={"sub": user.email, "user_id": str(user.id)})
        refresh_token = AuthService.create_refresh_token(user.id)
        
        # Invalidate old sessions (optional: keep only N recent sessions)
        old_sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_deleted == False
        ).order_by(UserSession.created_at.desc()).offset(10)  # Keep only 10 recent sessions
        
        for session in old_sessions:
            session.is_deleted = True
        
        # Create new session
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(session)
        db.commit()
        
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def refresh_token(db: Session, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        
        # Verify refresh token
        payload = AuthService.verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        # Find the session
        session = db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token,
            UserSession.is_deleted == False
        ).first()
        
        if not session or session.is_expired():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        new_access_token = AuthService.create_access_token(data={"sub": user.email, "user_id": str(user.id)})
        new_refresh_token = AuthService.create_refresh_token(user.id)
        
        # Update session
        session.session_token = new_access_token
        session.refresh_token = new_refresh_token
        session.expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        session.last_activity = datetime.now(timezone.utc)
        
        db.commit()
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def logout_user(db: Session, access_token: str) -> bool:
        """Logout user by invalidating session"""
        
        # Find and invalidate session
        session = db.query(UserSession).filter(
            UserSession.session_token == access_token,
            UserSession.is_deleted == False
        ).first()
        
        if session:
            session.is_deleted = True
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def logout_all_sessions(db: Session, user_id: str) -> int:
        """Logout user from all devices"""
        
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_deleted == False
        ).all()
        
        count = 0
        for session in sessions:
            session.is_deleted = True
            count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Get current user from access token"""
        
        payload = AuthService.verify_token(token, "access")
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user = db.query(User).filter(
            User.email == email,
            User.is_deleted == False,
            User.is_active == True
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
    
    @staticmethod
    def update_user_profile(db: Session, user_id: str, user_update: UserUpdate) -> User:
        """Update user profile information"""
        
        user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check for email/username conflicts
        update_data = user_update.dict(exclude_unset=True)
        
        if "email" in update_data:
            existing = db.query(User).filter(
                User.email == update_data["email"].lower(),
                User.id != user_id,
                User.is_deleted == False
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            update_data["email"] = update_data["email"].lower()
        
        if "username" in update_data:
            existing = db.query(User).filter(
                User.username == update_data["username"].lower(),
                User.id != user_id,
                User.is_deleted == False
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already in use"
                )
            update_data["username"] = update_data["username"].lower()
        
        # Update user
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def change_password(db: Session, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        
        user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not AuthService.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = AuthService.get_password_hash(new_password)
        
        # Invalidate all sessions except current one (force re-login on other devices)
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_deleted == False
        ).all()
        
        for session in sessions[1:]:  # Keep the first (current) session
            session.is_deleted = True
        
        db.commit()
        return True
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: str) -> list:
        """Get all active sessions for a user"""
        
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_deleted == False
        ).order_by(UserSession.last_activity.desc()).all()
        
        return [session for session in sessions if not session.is_expired()]