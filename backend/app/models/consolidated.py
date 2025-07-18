# backend/app/models/consolidated.py
# Updated with REAL PDF models for Stage 3.3

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, DECIMAL, Index, BigInteger, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from studysprint_db.config.database import Base
from studysprint_db.utils.mixins import MetadataMixin, ProgressMixin, ColorMixin, StatisticsMixin

# ============================================================================
# TOPIC MANAGEMENT MODELS (COMPLETED)
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
    
    # Relationships
    pdfs = relationship("PDF", back_populates="topic", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_topics_user_name', 'user_id', 'name'),
        Index('ix_topics_last_studied', 'user_id', 'last_studied_at'),
    )
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name}', user_id={self.user_id})>"

# ============================================================================
# PDF MANAGEMENT MODELS (STAGE 3.3 - NEW)
# ============================================================================

class PDF(Base, MetadataMixin, ProgressMixin, StatisticsMixin):
    """PDF documents and study materials"""
    __tablename__ = "pdfs"
    
    # Core fields
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False, index=True)
    
    # File information
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)  # Storage path
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    file_hash = Column(String(64), nullable=True, index=True)  # For duplicate detection
    mime_type = Column(String(100), default='application/pdf')
    
    # PDF metadata
    total_pages = Column(Integer, default=0, nullable=False)
    current_page = Column(Integer, default=1, nullable=False)
    pdf_version = Column(String(10))  # PDF version (1.4, 1.7, etc.)
    
    # Processing status
    upload_status = Column(String(20), default='completed', nullable=False)  # uploading, completed, failed
    processing_status = Column(String(20), default='pending', nullable=False)  # pending, processing, completed, failed
    
    # PDF type and organization
    pdf_type = Column(String(20), default='study', nullable=False)  # study, exercise, reference
    parent_pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=True)  # For exercise PDFs
    
    # Study tracking
    reading_position = Column(JSONB, default=dict)  # {page: X, scroll: Y, zoom: Z}
    bookmarks = Column(JSONB, default=list)  # User bookmarks
    notes_count = Column(Integer, default=0, nullable=False)
    highlights_count = Column(Integer, default=0, nullable=False)
    
    # Time estimates and analytics
    estimated_read_time = Column(Integer, default=0, nullable=False)  # minutes
    actual_read_time = Column(Integer, default=0, nullable=False)  # minutes spent
    difficulty_rating = Column(Integer, default=1, nullable=False)  # 1-5 scale
    
    # Relationships
    topic = relationship("Topic", back_populates="pdfs")
    exercise_sets = relationship("ExerciseSet", back_populates="main_pdf", cascade="all, delete-orphan")
    child_pdfs = relationship("PDF", backref="parent_pdf", remote_side="PDF.id")
    
    # Indexes
    __table_args__ = (
        Index('ix_pdfs_user_topic', 'user_id', 'topic_id'),
        Index('ix_pdfs_file_hash', 'file_hash'),
        Index('ix_pdfs_upload_status', 'upload_status'),
        Index('ix_pdfs_processing_status', 'processing_status'),
    )
    
    def __repr__(self):
        return f"<PDF(id={self.id}, title='{self.title}', topic_id={self.topic_id})>"
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def reading_progress_percentage(self) -> float:
        """Calculate reading progress percentage"""
        if self.total_pages == 0:
            return 0.0
        return round((self.current_page / self.total_pages) * 100, 2)
    
    def update_reading_position(self, page: int, scroll_y: float = 0, zoom: float = 1.0):
        """Update current reading position"""
        self.current_page = max(1, min(page, self.total_pages))
        if not self.reading_position:
            self.reading_position = {}
        self.reading_position.update({
            'page': self.current_page,
            'scroll_y': scroll_y,
            'zoom': zoom,
            'updated_at': datetime.now(timezone.utc).isoformat()
        })

class ExerciseSet(Base, MetadataMixin, ProgressMixin):
    """Collection of exercises for a PDF"""
    __tablename__ = "exercise_sets"
    
    # Core fields
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    main_pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=False, index=True)
    
    # Exercise set information
    title = Column(String(255), nullable=False)
    description = Column(Text)
    difficulty_level = Column(Integer, default=1, nullable=False)  # 1-5 scale
    estimated_time_minutes = Column(Integer, default=60, nullable=False)
    
    # Progress tracking
    total_exercises = Column(Integer, default=0, nullable=False)
    completed_exercises = Column(Integer, default=0, nullable=False)
    
    # Organization
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    main_pdf = relationship("PDF", back_populates="exercise_sets")
    exercises = relationship("Exercise", back_populates="exercise_set", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_exercise_sets_user_pdf', 'user_id', 'main_pdf_id'),
        Index('ix_exercise_sets_display_order', 'main_pdf_id', 'display_order'),
    )
    
    def __repr__(self):
        return f"<ExerciseSet(id={self.id}, title='{self.title}', main_pdf_id={self.main_pdf_id})>"
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_exercises == 0:
            return 0.0
        return round((self.completed_exercises / self.total_exercises) * 100, 2)

class Exercise(Base, MetadataMixin, ProgressMixin):
    """Individual exercise within an exercise set"""
    __tablename__ = "exercises"
    
    # Core fields
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    exercise_set_id = Column(UUID(as_uuid=True), ForeignKey("exercise_sets.id"), nullable=False, index=True)
    exercise_pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=True, index=True)
    
    # Exercise information
    title = Column(String(255), nullable=False)
    description = Column(Text)
    difficulty_level = Column(Integer, default=1, nullable=False)  # 1-5 scale
    estimated_time_minutes = Column(Integer, default=30, nullable=False)
    points_possible = Column(Integer, default=100, nullable=False)
    
    # Progress and results
    user_score = Column(Integer, nullable=True)  # Score achieved
    completion_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text)  # User notes for this exercise
    
    # Organization
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    exercise_set = relationship("ExerciseSet", back_populates="exercises")
    exercise_pdf = relationship("PDF", foreign_keys=[exercise_pdf_id])
    page_links = relationship("ExercisePageLink", back_populates="exercise", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_exercises_user_set', 'user_id', 'exercise_set_id'),
        Index('ix_exercises_completion', 'is_completed', 'completion_date'),
        Index('ix_exercises_display_order', 'exercise_set_id', 'display_order'),
    )
    
    def __repr__(self):
        return f"<Exercise(id={self.id}, title='{self.title}', exercise_set_id={self.exercise_set_id})>"
    
    @property
    def score_percentage(self) -> float:
        """Calculate score as percentage"""
        if not self.user_score or self.points_possible == 0:
            return 0.0
        return round((self.user_score / self.points_possible) * 100, 2)

class ExercisePageLink(Base):
    """Links exercises to specific pages in main PDFs"""
    __tablename__ = "exercise_page_links"
    
    # Core fields
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.id"), nullable=False, index=True)
    main_pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    
    # Link metadata
    link_type = Column(String(20), default='related', nullable=False)  # related, prerequisite, practice
    relevance_score = Column(DECIMAL(3, 2), default=1.0, nullable=False)  # 0-1 scale
    description = Column(Text)  # Why this page is linked
    
    # Relationships
    exercise = relationship("Exercise", back_populates="page_links")
    main_pdf = relationship("PDF", foreign_keys=[main_pdf_id])
    
    # Indexes
    __table_args__ = (
        Index('ix_exercise_page_links_exercise_page', 'exercise_id', 'page_number'),
        Index('ix_exercise_page_links_pdf_page', 'main_pdf_id', 'page_number'),
        Index('ix_exercise_page_links_type', 'link_type'),
    )
    
    def __repr__(self):
        return f"<ExercisePageLink(exercise_id={self.exercise_id}, page={self.page_number})>"

# ============================================================================
# PLACEHOLDER MODELS FOR FUTURE STAGES
# ============================================================================

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