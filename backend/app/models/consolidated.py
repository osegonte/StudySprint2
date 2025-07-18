# backend/app/models.py
# Consolidated SQLAlchemy models for all StudySprint domains

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, DECIMAL, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from studysprint_db.config.database import Base
from studysprint_db.utils.mixins import MetadataMixin, ProgressMixin, ColorMixin, StatisticsMixin

# ============================================================================
# TOPIC MANAGEMENT MODELS
# ============================================================================

class Topic(Base, MetadataMixin, ColorMixin, StatisticsMixin):
    """Topics for organizing PDFs and study materials"""
    __tablename__ = "topics"
    
    # Core fields
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Statistics (denormalized for performance)
    total_pdfs = Column(Integer, default=0, nullable=False)
    total_exercises = Column(Integer, default=0, nullable=False)
    total_pages = Column(Integer, default=0, nullable=False)
    study_progress = Column(DECIMAL(5, 2), default=0.0, nullable=False)  # 0-100%
    estimated_completion_hours = Column(Integer, default=0, nullable=False)
    
    # Study tracking
    last_studied_at = Column(DateTime(timezone=True))
    total_study_time = Column(Integer, default=0, nullable=False)  # minutes
    
    # Indexes
    __table_args__ = (
        Index('ix_topics_user_name', 'user_id', 'name'),
        Index('ix_topics_last_studied', 'user_id', 'last_studied_at'),
    )
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name}', user_id={self.user_id})>"

# Placeholder classes for future stages - these will be implemented later
class PDF(Base):
    """Placeholder - will be implemented in Stage 3.3"""
    __tablename__ = "pdfs_placeholder"
    placeholder = Column(String(1), default="x")

class ExerciseSet(Base):
    """Placeholder - will be implemented in Stage 3.3"""
    __tablename__ = "exercise_sets_placeholder"
    placeholder = Column(String(1), default="x")

class Exercise(Base):
    """Placeholder - will be implemented in Stage 3.3"""
    __tablename__ = "exercises_placeholder"
    placeholder = Column(String(1), default="x")

class ExercisePageLink(Base):
    """Placeholder - will be implemented in Stage 3.3"""
    __tablename__ = "exercise_page_links_placeholder"
    placeholder = Column(String(1), default="x")

class StudySession(Base):
    """Placeholder - will be implemented in Stage 3.4"""
    __tablename__ = "study_sessions_placeholder"
    placeholder = Column(String(1), default="x")

class PageTime(Base):
    """Placeholder - will be implemented in Stage 3.4"""
    __tablename__ = "page_times_placeholder"
    placeholder = Column(String(1), default="x")

class PomodoroSession(Base):
    """Placeholder - will be implemented in Stage 3.4"""
    __tablename__ = "pomodoro_sessions_placeholder"
    placeholder = Column(String(1), default="x")

class Note(Base):
    """Placeholder - will be implemented in Stage 3.5"""
    __tablename__ = "notes_placeholder"
    placeholder = Column(String(1), default="x")

class NoteLink(Base):
    """Placeholder - will be implemented in Stage 3.5"""
    __tablename__ = "note_links_placeholder"
    placeholder = Column(String(1), default="x")

class NoteTag(Base):
    """Placeholder - will be implemented in Stage 3.5"""
    __tablename__ = "note_tags_placeholder"
    placeholder = Column(String(1), default="x")

class Highlight(Base):
    """Placeholder - will be implemented in Stage 3.5"""
    __tablename__ = "highlights_placeholder"
    placeholder = Column(String(1), default="x")

class NoteAttachment(Base):
    """Placeholder - will be implemented in Stage 3.5"""
    __tablename__ = "note_attachments_placeholder"
    placeholder = Column(String(1), default="x")

class ReadingSpeed(Base):
    """Placeholder - will be implemented in Stage 3.6"""
    __tablename__ = "reading_speeds_placeholder"
    placeholder = Column(String(1), default="x")

class TimeEstimate(Base):
    """Placeholder - will be implemented in Stage 3.6"""
    __tablename__ = "time_estimates_placeholder"
    placeholder = Column(String(1), default="x")

class UserStatistic(Base):
    """Placeholder - will be implemented in Stage 3.6"""
    __tablename__ = "user_statistics_placeholder"
    placeholder = Column(String(1), default="x")

class Goal(Base):
    """Placeholder - will be implemented in Stage 3.6"""
    __tablename__ = "goals_placeholder"
    placeholder = Column(String(1), default="x")

class GoalProgress(Base):
    """Placeholder - will be implemented in Stage 3.6"""
    __tablename__ = "goal_progress_placeholder"
    placeholder = Column(String(1), default="x")
