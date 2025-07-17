# StudySprint DB Package API Reference

> **Purpose**: This document provides everything needed to use the `studysprint-db` package without loading the entire codebase. Use this reference for future feature development.

## 📦 Quick Import Guide

```python
# Database Configuration
from studysprint_db.config.database import Base, create_database_engine, create_session_factory
from studysprint_db.config.settings import db_settings

# User Models
from studysprint_db.models.user import User, UserSession, UserPreferences

# User Schemas
from studysprint_db.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin, UserAuth, 
    UserPreferencesUpdate, UserPreferencesResponse, TokenResponse
)

# Utility Mixins
from studysprint_db.utils.mixins import (
    ProgressMixin, MetadataMixin, ColorMixin, StatisticsMixin,
    BaseContentMixin, BaseTrackingMixin
)
```

## 🗄️ Database Models

### User Model
```python
class User(Base):
    __tablename__ = "users"
    
    # Core Fields
    id: UUID (Primary Key)
    email: str (Unique, Indexed)
    username: str (Unique, Indexed) 
    hashed_password: str
    full_name: str (Optional)
    
    # Status Fields
    is_active: bool (Default: True)
    is_verified: bool (Default: False)
    is_superuser: bool (Default: False)
    subscription_tier: str (Default: 'free')
    subscription_expires_at: datetime (Optional)
    
    # Profile Fields
    avatar_url: str (Optional)
    timezone: str (Default: 'UTC')
    language: str (Default: 'en')
    
    # Statistics (Denormalized)
    total_study_time: int (Default: 0, minutes)
    total_pdfs: int (Default: 0)
    total_notes: int (Default: 0)
    current_streak: int (Default: 0)
    longest_streak: int (Default: 0)
    
    # Auto Fields (BaseModel)
    created_at: datetime (Auto)
    updated_at: datetime (Auto)
    is_deleted: bool (Default: False)
    
    # Relationships
    sessions: List[UserSession]
    preferences: UserPreferences (One-to-One)
    
    # Methods
    def is_premium() -> bool
    def update_statistics(study_time_minutes=0, pdfs_added=0, notes_added=0)
```

### UserSession Model
```python
class UserSession(Base):
    __tablename__ = "user_sessions"
    
    # Core Fields
    id: UUID (Primary Key)
    user_id: UUID (Foreign Key to users.id)
    session_token: str (Unique, Indexed)
    refresh_token: str (Unique, Indexed, Optional)
    expires_at: datetime
    last_activity: datetime (Auto)
    
    # Session Metadata
    ip_address: str (Optional, IPv6 compatible)
    user_agent: str (Optional)
    device_fingerprint: str (Optional)
    
    # Auto Fields
    created_at: datetime (Auto)
    updated_at: datetime (Auto)
    is_deleted: bool (Default: False)
    
    # Relationships
    user: User
    
    # Methods
    def is_expired() -> bool
    def is_active() -> bool
```

### UserPreferences Model
```python
class UserPreferences(Base, MetadataMixin):
    __tablename__ = "user_preferences"
    
    # Core Fields
    id: UUID (Primary Key)
    user_id: UUID (Foreign Key to users.id, Unique)
    
    # UI Preferences
    theme: str (Default: 'light') # 'light', 'dark', 'auto'
    sidebar_collapsed: bool (Default: False)
    language: str (Default: 'en')
    timezone: str (Default: 'UTC')
    
    # Study Preferences
    default_session_duration: int (Default: 25, minutes)
    break_duration: int (Default: 5, minutes)
    long_break_duration: int (Default: 15, minutes)
    auto_start_breaks: bool (Default: True)
    sound_enabled: bool (Default: True)
    
    # Notification Preferences
    email_notifications: bool (Default: True)
    goal_reminders: bool (Default: True)
    study_reminders: bool (Default: True)
    achievement_notifications: bool (Default: True)
    
    # Advanced Settings
    reading_speed_wpm: int (Default: 250)
    pdf_zoom_level: str (Default: '1.0')
    auto_save_notes: bool (Default: True)
    
    # From MetadataMixin
    metadata: JSONB (Default: {})
    
    # Auto Fields
    created_at: datetime (Auto)
    updated_at: datetime (Auto)
    is_deleted: bool (Default: False)
    
    # Relationships
    user: User
    
    # Methods
    def get_study_settings() -> dict
    # From MetadataMixin:
    def set_metadata(key: str, value: Any)
    def get_metadata(key: str, default: Any = None) -> Any
    def update_metadata(data: Dict[str, Any])
```

## 📋 Pydantic Schemas

### User Schemas
```python
# Creation/Update
class UserCreate(BaseModel):
    email: EmailStr
    username: str (3-100 chars, alphanumeric + _ -)
    password: str (min 8 chars)
    full_name: str (Optional)

class UserUpdate(BaseModel):
    email: EmailStr (Optional)
    username: str (Optional)
    full_name: str (Optional)
    avatar_url: str (Optional)
    timezone: str (Optional)
    language: str (Optional)

# Response
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: str (Optional)
    is_active: bool
    is_verified: bool
    subscription_tier: str
    avatar_url: str (Optional)
    timezone: str
    language: str
    total_study_time: int
    total_pdfs: int
    total_notes: int
    current_streak: int
    longest_streak: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### Authentication Schemas
```python
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserAuth(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
```

### Preferences Schemas
```python
class UserPreferencesUpdate(BaseModel):
    theme: str (Optional, pattern: '^(light|dark|auto)$')
    sidebar_collapsed: bool (Optional)
    language: str (Optional, max 10 chars)
    timezone: str (Optional, max 50 chars)
    default_session_duration: int (Optional, 5-120)
    break_duration: int (Optional, 1-30)
    long_break_duration: int (Optional, 5-60)
    auto_start_breaks: bool (Optional)
    sound_enabled: bool (Optional)
    email_notifications: bool (Optional)
    goal_reminders: bool (Optional)
    study_reminders: bool (Optional)
    achievement_notifications: bool (Optional)
    reading_speed_wpm: int (Optional, 50-1000)
    pdf_zoom_level: str (Optional)
    auto_save_notes: bool (Optional)

class UserPreferencesResponse(BaseModel):
    # All fields from UserPreferencesUpdate plus:
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

## 🧰 Utility Mixins

### Available Mixins
```python
# Progress Tracking
class ProgressMixin:
    progress_percentage: DECIMAL(5,2) (Default: 0.0)
    is_completed: bool (Default: False)
    completed_at: datetime (Optional)
    
    def update_progress(percentage: float)
    def mark_completed()
    def mark_incomplete()

# JSON Metadata Storage
class MetadataMixin:
    metadata: JSONB (Default: {})
    
    def set_metadata(key: str, value: Any)
    def get_metadata(key: str, default: Any = None) -> Any
    def update_metadata(data: Dict[str, Any])

# Color Customization
class ColorMixin:
    color: str (Default: '#3498db')
    
    def set_color(color: str)  # Validates hex format
    @property
    def color_rgb() -> tuple

# Statistics Tracking
class StatisticsMixin:
    view_count: int (Default: 0)
    last_viewed_at: datetime (Optional)
    
    def increment_views()

# Combined Mixins
class BaseContentMixin(MetadataMixin, StatisticsMixin):
    """For content-based models"""

class BaseTrackingMixin(ProgressMixin, StatisticsMixin):
    """For tracking-based models"""
```

## ⚙️ Database Configuration

### Settings
```python
# Database Settings Class
class DatabaseSettings:
    DATABASE_URL: str = "postgresql://studysprint:password@localhost:5433/studysprint2"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 300

# Global instance
db_settings = DatabaseSettings()
```

### Base Model
```python
# All models inherit from BaseModel
class BaseModel:
    id: UUID (Primary Key, Auto-generated)
    created_at: datetime (Auto, UTC)
    updated_at: datetime (Auto, UTC) 
    is_deleted: bool (Default: False, Soft Delete)
    
    def __repr__() -> str

# Declarative Base
Base = declarative_base(cls=BaseModel)
```

### Engine & Session Functions
```python
def create_database_engine(database_url: str, echo: bool = False, **kwargs):
    """Create SQLAlchemy engine with optimal settings"""
    # Returns configured engine with connection pooling

def create_session_factory(engine):
    """Create session factory for dependency injection"""
    # Returns sessionmaker with proper configuration

def get_table_info(engine):
    """Get information about database tables"""
    # Returns dict with table metadata
```

## 🎯 Usage Patterns for New Features

### Creating New Models
```python
from studysprint_db.config.database import Base
from studysprint_db.utils.mixins import ProgressMixin, MetadataMixin

class Topic(Base, MetadataMixin, ColorMixin):
    __tablename__ = "topics"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Relationships
    user = relationship("User")
    pdfs = relationship("PDF", back_populates="topic")
```

### Creating New Schemas
```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class TopicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern='^#[0-9A-Fa-f]{6}$')

class TopicResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    color: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### Database Integration in Backend
```python
# In backend/app/config/database.py
from studysprint_db.config.database import (
    Base, create_database_engine, create_session_factory
)
from studysprint_db.config.settings import db_settings

engine = create_database_engine(db_settings.DATABASE_URL)
SessionLocal = create_session_factory(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# In services
from sqlalchemy.orm import Session
from studysprint_db.models.user import User

class TopicService:
    @staticmethod
    def create_topic(db: Session, user_id: str, topic_data):
        # Service implementation
        pass
```

## 🔄 Migration Management

### Alembic Commands
```bash
# Create new migration
alembic revision --autogenerate -m "Add topic tables"

# Apply migrations
alembic upgrade head

# Check current migration
alembic current

# Show migration history
alembic history
```

### Adding New Models to Migrations
```python
# In studysprint_db/alembic/env.py, add imports:
from studysprint_db.models.topic import Topic
from studysprint_db.models.pdf import PDF
# etc.
```

## 📊 Current Database Schema

### Tables Created
- `users` - User accounts (15+ columns)
- `user_sessions` - Authentication sessions (10+ columns)  
- `user_preferences` - User settings (20+ columns)
- `alembic_version` - Migration tracking

### Foreign Key Pattern
- All foreign keys use UUID references
- CASCADE deletes for dependent data
- Proper indexing on foreign key columns

### Naming Conventions
- Tables: lowercase_with_underscores
- Columns: lowercase_with_underscores
- Relationships: descriptive names (user, sessions, preferences)

## 🚀 Ready for Stage 3

This database package provides the foundation for:
- **Topic Management** (organize PDFs by subject)
- **PDF Management** (upload, store, metadata)
- **Exercise System** (attach exercises to PDFs) 
- **Session Tracking** (time tracking, analytics)
- **Notes System** (Obsidian-style linking)

The architecture supports adding new models while maintaining the existing user authentication system.