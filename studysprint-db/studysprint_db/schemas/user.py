"""User-related Pydantic schemas"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None

# User creation schemas
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        # Allow alphanumeric plus underscore and hyphen
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (with _ and - allowed)')
        return v.lower()
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if v is not None:
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Username must be alphanumeric (with _ and - allowed)')
            return v.lower()
        return v
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower() if v else v

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    subscription_tier: str
    avatar_url: Optional[str]
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

# Authentication schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()

class UserAuth(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

# Preferences schemas
class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = Field(None, pattern='^(light|dark|auto)$')
    sidebar_collapsed: Optional[bool] = None
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    default_session_duration: Optional[int] = Field(None, ge=5, le=120)
    break_duration: Optional[int] = Field(None, ge=1, le=30)
    long_break_duration: Optional[int] = Field(None, ge=5, le=60)
    auto_start_breaks: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    goal_reminders: Optional[bool] = None
    study_reminders: Optional[bool] = None
    achievement_notifications: Optional[bool] = None
    reading_speed_wpm: Optional[int] = Field(None, ge=50, le=1000)
    pdf_zoom_level: Optional[str] = None
    auto_save_notes: Optional[bool] = None

class UserPreferencesResponse(BaseModel):
    id: UUID
    user_id: UUID
    theme: str
    sidebar_collapsed: bool
    language: str
    timezone: str
    default_session_duration: int
    break_duration: int
    long_break_duration: int
    auto_start_breaks: bool
    sound_enabled: bool
    email_notifications: bool
    goal_reminders: bool
    study_reminders: bool
    achievement_notifications: bool
    reading_speed_wpm: int
    pdf_zoom_level: str
    auto_save_notes: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Session schemas
class UserSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    expires_at: datetime
    last_activity: datetime
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
