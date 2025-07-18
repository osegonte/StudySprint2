# backend/app/models/consolidated.py
# Updated with Timer & Analytics models for Stage 3.4

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
    study_sessions = relationship("StudySession", back_populates="topic", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_topics_user_name', 'user_id', 'name'),
        Index('ix_topics_last_studied', 'user_id', 'last_studied_at'),
    )
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name}', user_id={self.user_id})>"

# ============================================================================
# PDF MANAGEMENT MODELS (COMPLETED)
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
    study_sessions = relationship("StudySession", back_populates="pdf", cascade="all, delete-orphan")
    page_times = relationship("PageTime", back_populates="pdf", cascade="all, delete-orphan")
    
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
# TIMER & ANALYTICS MODELS (STAGE 3.4 - NEW)
# ============================================================================

class StudySession(Base, MetadataMixin):
    """Main study session container with comprehensive tracking"""
    __tablename__ = "study_sessions"
    
    # Core fields
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=False, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False, index=True)
    
    # Session metadata
    session_type = Column(String(20), default='study', nullable=False)  # study, exercise, review, pomodoro
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Time tracking
    total_minutes = Column(Integer, default=0, nullable=False)
    active_minutes = Column(Integer, default=0, nullable=False)
    idle_minutes = Column(Integer, default=0, nullable=False)
    break_minutes = Column(Integer, default=0, nullable=False)
    
    # Activity tracking
    pages_visited = Column(Integer, default=0, nullable=False)
    pages_completed = Column(Integer, default=0, nullable=False)
    clicks_count = Column(Integer, default=0, nullable=False)
    scroll_events = Column(Integer, default=0, nullable=False)
    interruptions = Column(Integer, default=0, nullable=False)
    
    # Pomodoro tracking
    pomodoro_cycles = Column(Integer, default=0, nullable=False)
    planned_cycles = Column(Integer, default=0, nullable=False)
    
    # Performance metrics
    focus_score = Column(DECIMAL(3, 2), default=0.0, nullable=False)  # 0-1 scale
    productivity_score = Column(DECIMAL(3, 2), default=0.0, nullable=False)  # 0-1 scale
    comprehension_score = Column(DECIMAL(3, 2), default=0.0, nullable=False)  # 0-1 scale
    
    # Gamification
    xp_earned = Column(Integer, default=0, nullable=False)
    achievements_unlocked = Column(JSONB, default=list)
    
    # Session state
    is_active = Column(Boolean, default=True, nullable=False)
    is_paused = Column(Boolean, default=False, nullable=False)
    pause_count = Column(Integer, default=0, nullable=False)
    
    # Notes and feedback
    notes = Column(Text)
    session_rating = Column(Integer, nullable=True)  # 1-5 user rating
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    pdf = relationship("PDF", back_populates="study_sessions")
    topic = relationship("Topic", back_populates="study_sessions")
    page_times = relationship("PageTime", back_populates="session", cascade="all, delete-orphan")
    pomodoro_sessions = relationship("PomodoroSession", back_populates="study_session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_study_sessions_user_date', 'user_id', 'start_time'),
        Index('ix_study_sessions_pdf_date', 'pdf_id', 'start_time'),
        Index('ix_study_sessions_active', 'is_active', 'is_paused'),
        Index('ix_study_sessions_type', 'session_type'),
    )
    
    def __repr__(self):
        return f"<StudySession(id={self.id}, user_id={self.user_id}, pdf_id={self.pdf_id})>"
    
    @property
    def duration_minutes(self) -> int:
        """Calculate total session duration"""
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        elif self.is_active:
            delta = datetime.now(timezone.utc) - self.start_time
            return int(delta.total_seconds() / 60)
        return self.total_minutes
    
    @property
    def efficiency_score(self) -> float:
        """Calculate session efficiency (active time / total time)"""
        if self.total_minutes == 0:
            return 0.0
        return round(self.active_minutes / self.total_minutes, 2)
    
    def end_session(self) -> None:
        """End the study session and calculate final metrics"""
        self.end_time = datetime.now(timezone.utc)
        self.is_active = False
        self.is_paused = False
        self.total_minutes = self.duration_minutes
        
        # Calculate performance scores
        self.focus_score = self._calculate_focus_score()
        self.productivity_score = self._calculate_productivity_score()
        self.xp_earned = self._calculate_xp_earned()
    
    def _calculate_focus_score(self) -> float:
        """Calculate focus score based on interruptions and idle time"""
        if self.total_minutes == 0:
            return 0.0
        
        # Base score starts at 1.0
        score = 1.0
        
        # Reduce score for interruptions
        if self.interruptions > 0:
            score -= min(0.5, self.interruptions * 0.1)
        
        # Reduce score for excessive idle time
        if self.total_minutes > 0:
            idle_ratio = self.idle_minutes / self.total_minutes
            if idle_ratio > 0.2:  # More than 20% idle
                score -= min(0.3, (idle_ratio - 0.2) * 1.5)
        
        return max(0.0, round(score, 2))
    
    def _calculate_productivity_score(self) -> float:
        """Calculate productivity score based on pages and activity"""
        if self.total_minutes == 0:
            return 0.0
        
        # Base score from pages completed
        pages_score = min(1.0, self.pages_completed / max(1, self.total_minutes / 10))
        
        # Activity score from clicks and scrolls
        activity_score = min(1.0, (self.clicks_count + self.scroll_events) / max(1, self.total_minutes * 5))
        
        # Combine scores
        return round((pages_score * 0.7 + activity_score * 0.3), 2)
    
    def _calculate_xp_earned(self) -> int:
        """Calculate XP earned based on session performance"""
        base_xp = self.active_minutes * 2  # 2 XP per active minute
        
        # Bonus for focus
        focus_bonus = int(self.focus_score * 50)
        
        # Bonus for productivity
        productivity_bonus = int(self.productivity_score * 50)
        
        # Bonus for completing pages
        completion_bonus = self.pages_completed * 10
        
        # Bonus for pomodoro cycles
        pomodoro_bonus = self.pomodoro_cycles * 25
        
        return base_xp + focus_bonus + productivity_bonus + completion_bonus + pomodoro_bonus

class PageTime(Base):
    """Detailed page-level timing and analytics"""
    __tablename__ = "page_times"
    
    # Core fields
    session_id = Column(UUID(as_uuid=True), ForeignKey("study_sessions.id"), nullable=False, index=True)
    pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    
    # Time tracking
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    active_time_seconds = Column(Integer, default=0, nullable=False)
    idle_time_seconds = Column(Integer, default=0, nullable=False)
    
    # Activity tracking
    activity_count = Column(Integer, default=0, nullable=False)  # Clicks, scrolls, etc.
    click_count = Column(Integer, default=0, nullable=False)
    scroll_count = Column(Integer, default=0, nullable=False)
    zoom_changes = Column(Integer, default=0, nullable=False)
    
    # Reading analytics
    reading_speed_wpm = Column(DECIMAL(5, 2), nullable=True)  # Words per minute
    estimated_words = Column(Integer, default=0, nullable=False)
    difficulty_rating = Column(Integer, default=1, nullable=False)  # 1-5 scale (auto-calculated)
    comprehension_estimate = Column(DECIMAL(3, 2), default=0.0, nullable=False)  # 0-1 scale
    
    # Content interaction
    notes_created = Column(Integer, default=0, nullable=False)
    highlights_made = Column(Integer, default=0, nullable=False)
    bookmarks_added = Column(Integer, default=0, nullable=False)
    
    # Position tracking
    scroll_positions = Column(JSONB, default=list)  # Track scroll positions over time
    zoom_levels = Column(JSONB, default=list)  # Track zoom changes over time
    
    # Relationships
    session = relationship("StudySession", back_populates="page_times")
    pdf = relationship("PDF", back_populates="page_times")
    
    # Indexes
    __table_args__ = (
        Index('ix_page_times_session_page', 'session_id', 'page_number'),
        Index('ix_page_times_pdf_page', 'pdf_id', 'page_number'),
        Index('ix_page_times_duration', 'duration_seconds'),
    )
    
    def __repr__(self):
        return f"<PageTime(session_id={self.session_id}, page={self.page_number})>"
    
    @property
    def reading_speed_pages_per_hour(self) -> float:
        """Calculate reading speed in pages per hour"""
        if self.duration_seconds == 0:
            return 0.0
        
        hours = self.duration_seconds / 3600
        return round(1 / hours, 2)
    
    @property
    def engagement_score(self) -> float:
        """Calculate engagement score based on activity"""
        if self.duration_seconds == 0:
            return 0.0
        
        # Base score from activity frequency
        activity_rate = self.activity_count / (self.duration_seconds / 60)  # per minute
        
        # Normalize to 0-1 scale (optimal is 2-5 activities per minute)
        if activity_rate < 2:
            return activity_rate / 2
        elif activity_rate <= 5:
            return 1.0
        else:
            return max(0.5, 1.0 - (activity_rate - 5) * 0.1)
    
    def end_page_timing(self) -> None:
        """End page timing and calculate final metrics"""
        self.end_time = datetime.now(timezone.utc)
        if self.start_time:
            delta = self.end_time - self.start_time
            self.duration_seconds = int(delta.total_seconds())
        
        # Calculate reading speed if we have word estimates
        if self.estimated_words > 0 and self.active_time_seconds > 0:
            minutes = self.active_time_seconds / 60
            self.reading_speed_wpm = round(self.estimated_words / minutes, 2)
        
        # Auto-calculate difficulty based on time spent
        self.difficulty_rating = self._calculate_difficulty_rating()
        
        # Calculate comprehension estimate
        self.comprehension_estimate = self._calculate_comprehension_estimate()
    
    def _calculate_difficulty_rating(self) -> int:
        """Auto-calculate difficulty rating based on time spent"""
        if self.duration_seconds == 0:
            return 1
        
        # Use average time per page as baseline (2 minutes = easy)
        minutes_spent = self.duration_seconds / 60
        
        if minutes_spent < 1:
            return 1
        elif minutes_spent < 2:
            return 2
        elif minutes_spent < 4:
            return 3
        elif minutes_spent < 8:
            return 4
        else:
            return 5
    
    def _calculate_comprehension_estimate(self) -> float:
        """Estimate comprehension based on engagement and time"""
        engagement = self.engagement_score
        
        # Factor in note-taking and highlighting
        content_interaction = min(1.0, (self.notes_created + self.highlights_made) / 3)
        
        # Combine factors
        return round((engagement * 0.7 + content_interaction * 0.3), 2)

class PomodoroSession(Base):
    """Individual Pomodoro cycles within study sessions"""
    __tablename__ = "pomodoro_sessions"
    
    # Core fields
    study_session_id = Column(UUID(as_uuid=True), ForeignKey("study_sessions.id"), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False)
    
    # Cycle information
    cycle_type = Column(String(20), nullable=False)  # work, short_break, long_break
    planned_duration_minutes = Column(Integer, nullable=False)
    actual_duration_minutes = Column(Integer, default=0, nullable=False)
    
    # Time tracking
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    completed = Column(Boolean, default=False, nullable=False)
    interrupted = Column(Boolean, default=False, nullable=False)
    interruptions = Column(Integer, default=0, nullable=False)
    
    # Performance
    effectiveness_rating = Column(Integer, nullable=True)  # 1-5 user rating
    productivity_score = Column(DECIMAL(3, 2), default=0.0, nullable=False)
    focus_score = Column(DECIMAL(3, 2), default=0.0, nullable=False)
    
    # Gamification
    xp_earned = Column(Integer, default=0, nullable=False)
    
    # Relationships
    study_session = relationship("StudySession", back_populates="pomodoro_sessions")
    
    # Indexes
    __table_args__ = (
        Index('ix_pomodoro_sessions_study_session', 'study_session_id', 'cycle_number'),
        Index('ix_pomodoro_sessions_type', 'cycle_type'),
        Index('ix_pomodoro_sessions_completion', 'completed', 'completed_at'),
    )
    
    def __repr__(self):
        return f"<PomodoroSession(study_session_id={self.study_session_id}, cycle={self.cycle_number})>"
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if self.planned_duration_minutes == 0:
            return 0.0
        return round((self.actual_duration_minutes / self.planned_duration_minutes) * 100, 2)
    
    def complete_cycle(self, effectiveness_rating: int = None) -> None:
        """Complete the Pomodoro cycle"""
        self.completed_at = datetime.now(timezone.utc)
        self.completed = True
        
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.actual_duration_minutes = int(delta.total_seconds() / 60)
        
        if effectiveness_rating:
            self.effectiveness_rating = effectiveness_rating
        
        # Calculate scores
        self.productivity_score = self._calculate_productivity_score()
        self.focus_score = self._calculate_focus_score()
        self.xp_earned = self._calculate_xp_earned()
    
    def _calculate_productivity_score(self) -> float:
        """Calculate productivity score for this cycle"""
        if self.planned_duration_minutes == 0:
            return 0.0
        
        # Base score from completion
        completion_score = min(1.0, self.actual_duration_minutes / self.planned_duration_minutes)
        
        # Penalty for interruptions
        interruption_penalty = min(0.5, self.interruptions * 0.1)
        
        return max(0.0, round(completion_score - interruption_penalty, 2))
    
    def _calculate_focus_score(self) -> float:
        """Calculate focus score for this cycle"""
        if self.cycle_type != 'work':
            return 1.0  # Breaks are always considered focused
        
        # Base score
        score = 1.0
        
        # Reduce for interruptions
        if self.interruptions > 0:
            score -= min(0.8, self.interruptions * 0.2)
        
        # Bonus for completing full cycle
        if self.completed and self.actual_duration_minutes >= self.planned_duration_minutes:
            score += 0.1
        
        return max(0.0, min(1.0, round(score, 2)))
    
    def _calculate_xp_earned(self) -> int:
        """Calculate XP earned for this cycle"""
        if self.cycle_type == 'work':
            base_xp = 25 if self.completed else 10
            focus_bonus = int(self.focus_score * 15)
            productivity_bonus = int(self.productivity_score * 10)
            return base_xp + focus_bonus + productivity_bonus
        else:
            # Breaks earn smaller XP
            return 5 if self.completed else 2

class ReadingSpeed(Base):
    """Reading speed analytics and tracking"""
    __tablename__ = "reading_speeds"
    
    # Core fields
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=True, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("study_sessions.id"), nullable=True, index=True)
    
    # Speed metrics
    pages_per_minute = Column(DECIMAL(5, 2), nullable=False)
    words_per_minute = Column(DECIMAL(5, 2), nullable=False)
    characters_per_minute = Column(DECIMAL(7, 2), nullable=False)
    
    # Content characteristics
    content_type = Column(String(50), default='mixed', nullable=False)  # text, math, diagram, mixed
    difficulty_level = Column(Integer, default=1, nullable=False)  # 1-5 scale
    estimated_words = Column(Integer, default=0, nullable=False)
    
    # Context factors
    time_of_day = Column(Integer, nullable=False)  # Hour 0-23
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday=0)
    session_duration = Column(Integer, nullable=False)  # Minutes
    
    # Environmental factors
    environmental_factors = Column(JSONB, default=dict)  # distractions, noise, etc.
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    pdf = relationship("PDF", foreign_keys=[pdf_id])
    topic = relationship("Topic", foreign_keys=[topic_id])
    session = relationship("StudySession", foreign_keys=[session_id])
    
    # Indexes
    __table_args__ = (
        Index('ix_reading_speeds_user_date', 'user_id', 'created_at'),
        Index('ix_reading_speeds_content_type', 'content_type', 'difficulty_level'),
        Index('ix_reading_speeds_context', 'time_of_day', 'day_of_week'),
    )
    
    def __repr__(self):
        return f"<ReadingSpeed(user_id={self.user_id}, wpm={self.words_per_minute})>"

class TimeEstimate(Base):
    """Smart time estimation and predictions"""
    __tablename__ = "time_estimates"
    
    # Core fields
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    pdf_id = Column(UUID(as_uuid=True), ForeignKey("pdfs.id"), nullable=True, index=True)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True, index=True)
    
    # Estimate information
    estimate_type = Column(String(20), nullable=False)  # completion, session, daily_target, page
    estimated_minutes = Column(Integer, nullable=False)
    estimated_sessions = Column(Integer, default=1, nullable=False)
    
    # Confidence and accuracy
    confidence_level = Column(String(20), default='medium', nullable=False)  # low, medium, high
    confidence_score = Column(DECIMAL(3, 2), default=0.5, nullable=False)  # 0-1 scale
    accuracy_score = Column(DECIMAL(3, 2), nullable=True)  # How accurate past estimates were
    
    # Data sources
    based_on_sessions = Column(Integer, default=0, nullable=False)
    based_on_pages = Column(Integer, default=0, nullable=False)
    factors_used = Column(JSONB, default=dict)  # What data was used for estimation
    
    # Validity
    valid_until = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Actual vs estimated (for accuracy tracking)
    actual_minutes = Column(Integer, nullable=True)
    variance_percentage = Column(DECIMAL(5, 2), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    pdf = relationship("PDF", foreign_keys=[pdf_id])
    topic = relationship("Topic", foreign_keys=[topic_id])
    
    # Indexes
    __table_args__ = (
        Index('ix_time_estimates_user_type', 'user_id', 'estimate_type'),
        Index('ix_time_estimates_validity', 'is_active', 'valid_until'),
        Index('ix_time_estimates_accuracy', 'accuracy_score'),
    )
    
    def __repr__(self):
        return f"<TimeEstimate(user_id={self.user_id}, type={self.estimate_type}, minutes={self.estimated_minutes})>"
    
    @property
    def estimated_hours(self) -> float:
        """Get estimated time in hours"""
        return round(self.estimated_minutes / 60, 2)
    
    @property
    def is_expired(self) -> bool:
        """Check if estimate is expired"""
        if not self.valid_until:
            return False
        return datetime.now(timezone.utc) > self.valid_until
    
    def update_accuracy(self, actual_minutes: int) -> None:
        """Update accuracy based on actual time taken"""
        self.actual_minutes = actual_minutes
        
        if self.estimated_minutes > 0:
            variance = abs(actual_minutes - self.estimated_minutes) / self.estimated_minutes
            self.variance_percentage = round(variance * 100, 2)
            
            # Calculate accuracy score (1.0 = perfect, 0.0 = terrible)
            if variance <= 0.1:  # Within 10%
                self.accuracy_score = 1.0
            elif variance <= 0.25:  # Within 25%
                self.accuracy_score = 0.8
            elif variance <= 0.5:  # Within 50%
                self.accuracy_score = 0.6
            elif variance <= 1.0:  # Within 100%
                self.accuracy_score = 0.4
            else:
                self.accuracy_score = 0.2

class UserStatistic(Base):
    """User-level statistics and analytics"""
    __tablename__ = "user_statistics"
    
    # Core fields
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    stat_type = Column(String(50), nullable=False)  # daily, weekly, monthly, lifetime
    stat_date = Column(DateTime(timezone=True), nullable=False)
    
    # Study metrics
    total_study_minutes = Column(Integer, default=0, nullable=False)
    total_active_minutes = Column(Integer, default=0, nullable=False)
    total_sessions = Column(Integer, default=0, nullable=False)
    pages_read = Column(Integer, default=0, nullable=False)
    
    # Performance metrics
    average_focus_score = Column(DECIMAL(3, 2), default=0.0, nullable=False)
    average_productivity_score = Column(DECIMAL(3, 2), default=0.0, nullable=False)
    average_reading_speed = Column(DECIMAL(5, 2), default=0.0, nullable=False)
    
    # Engagement metrics
    notes_created = Column(Integer, default=0, nullable=False)
    highlights_made = Column(Integer, default=0, nullable=False)
    bookmarks_added = Column(Integer, default=0, nullable=False)
    exercises_completed = Column(Integer, default=0, nullable=False)
    
    # Streaks and consistency
    study_streak = Column(Integer, default=0, nullable=False)
    consistency_score = Column(DECIMAL(3, 2), default=0.0, nullable=False)
    
    # Pomodoro metrics
    pomodoro_cycles_completed = Column(Integer, default=0, nullable=False)
    pomodoro_success_rate = Column(DECIMAL(3, 2), default=0.0, nullable=False)
    
    # XP and achievements
    xp_earned = Column(Integer, default=0, nullable=False)
    level_achieved = Column(Integer, default=1, nullable=False)
    achievements_unlocked = Column(JSONB, default=list)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    # Indexes
    __table_args__ = (
        Index('ix_user_statistics_user_type_date', 'user_id', 'stat_type', 'stat_date'),
        Index('ix_user_statistics_date', 'stat_date'),
    )
    
    def __repr__(self):
        return f"<UserStatistic(user_id={self.user_id}, type={self.stat_type}, date={self.stat_date})>"
    
    @property
    def efficiency_score(self) -> float:
        """Calculate overall efficiency score"""
        if self.total_study_minutes == 0:
            return 0.0
        
        active_ratio = self.total_active_minutes / self.total_study_minutes
        return round((active_ratio + self.average_focus_score + self.average_productivity_score) / 3, 2)
    
    @property
    def daily_average_minutes(self) -> float:
        """Calculate daily average study time"""
        if self.stat_type == 'daily':
            return self.total_study_minutes
        elif self.stat_type == 'weekly':
            return round(self.total_study_minutes / 7, 2)
        elif self.stat_type == 'monthly':
            return round(self.total_study_minutes / 30, 2)
        return 0.0

# ============================================================================
# PLACEHOLDER MODELS FOR FUTURE STAGES
# ============================================================================

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

class Goal(Base):
    """Placeholder - will be implemented in Stage 3.6"""
    __tablename__ = "goals_placeholder"
    placeholder = Column(String(1), default="x")

class GoalProgress(Base):
    """Placeholder - will be implemented in Stage 3.6"""
    __tablename__ = "goal_progress_placeholder"
    placeholder = Column(String(1), default="x")