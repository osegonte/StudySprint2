"""User service using studysprint-db package"""

from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from studysprint_db.models.user import User, UserPreferences
from studysprint_db.schemas.user import UserCreate, UserUpdate

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """User management service"""
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email, User.is_deleted == False).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username, User.is_deleted == False).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        if UserService.get_user_by_email(db, user_create.email):
            raise ValueError("Email already registered")
        
        if UserService.get_user_by_username(db, user_create.username):
            raise ValueError("Username already taken")
        
        # Create user
        hashed_password = UserService.get_password_hash(user_create.password)
        
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            full_name=user_create.full_name
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create default preferences
        preferences = UserPreferences(user_id=db_user.id)
        db.add(preferences)
        db.commit()
        
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user by email and password"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        
        if not UserService.verify_password(password, user.hashed_password):
            return None
        
        return user
