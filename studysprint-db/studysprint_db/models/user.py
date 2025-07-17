"""User-related database models"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from studysprint_db.config.database import Base
from studysprint_db.utils.mixins import MetadataMixin

class User(Base):
    """Main user model"""
    __tablename__ = "users"
    
    # Core user fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Subscription
    subscription_tier = Column(String(20), default='free', nullable=False)  # free, premium, pro
    subscription_expires_at = Column(DateTime(timezone=True))
    
    # Profile
    avatar_url = Column(String(500))
    timezone = Column(String(50), default='UTC', nullable=False)
    language = Column(String(10), default='en', nullable=False)
    
    # Statistics (denormalized for performance)
    total_study_time = Column(Integer, default=0, nullable=False)  # minutes
    total_pdfs = Column(Integer, default=0, nullable=False)
    total_notes = Column(Integer, default=0, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def is_premium(self) -> bool:
        """Check if user has premium subscription"""
        if self.subscription_tier in ['premium', 'pro']:
            if self.subscription_expires_at:
                return self.subscription_expires_at > datetime.now(timezone.utc)
            return True
        return False
    
    def update_statistics(self, study_time_minutes: int = 0, pdfs_added: int = 0, notes_added: int = 0):
        """Update user statistics"""
        if study_time_minutes > 0:
            self.total_study_time += study_time_minutes
        if pdfs_added > 0:
            self.total_pdfs += pdfs_added
        if notes_added > 0:
            self.total_notes += notes_added

class UserSession(Base):
    """User authentication sessions"""
    __tablename__ = "user_sessions"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Session metadata
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    device_fingerprint = Column(String(255))
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_active(self) -> bool:
        """Check if session is active (not expired and not deleted)"""
        return not self.is_expired() and not self.is_deleted

class UserPreferences(Base, MetadataMixin):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # UI Preferences
    theme = Column(String(20), default='light', nullable=False)  # light, dark, auto
    sidebar_collapsed = Column(Boolean, default=False, nullable=False)
    language = Column(String(10), default='en', nullable=False)
    timezone = Column(String(50), default='UTC', nullable=False)
    
    # Study Preferences
    default_session_duration = Column(Integer, default=25, nullable=False)  # Pomodoro default
    break_duration = Column(Integer, default=5, nullable=False)
    long_break_duration = Column(Integer, default=15, nullable=False)
    auto_start_breaks = Column(Boolean, default=True, nullable=False)
    sound_enabled = Column(Boolean, default=True, nullable=False)
    
    # Notification Preferences
    email_notifications = Column(Boolean, default=True, nullable=False)
    goal_reminders = Column(Boolean, default=True, nullable=False)
    study_reminders = Column(Boolean, default=True, nullable=False)
    achievement_notifications = Column(Boolean, default=True, nullable=False)
    
    # Advanced Settings
    reading_speed_wpm = Column(Integer, default=250, nullable=False)  # Words per minute
    pdf_zoom_level = Column(String(10), default='1.0', nullable=False)  # Changed from DECIMAL to String for simplicity
    auto_save_notes = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(id={self.id}, user_id={self.user_id})>"
    
    def get_study_settings(self) -> dict:
        """Get study-related settings as dictionary"""
        return {
            'default_session_duration': self.default_session_duration,
            'break_duration': self.break_duration,
            'long_break_duration': self.long_break_duration,
            'auto_start_breaks': self.auto_start_breaks,
            'sound_enabled': self.sound_enabled,
            'reading_speed_wpm': self.reading_speed_wpm,
        }
