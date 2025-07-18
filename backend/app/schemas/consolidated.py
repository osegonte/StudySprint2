# backend/app/schemas/consolidated.py
# Updated with Timer & Analytics schemas for Stage 3.4

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from decimal import Decimal

# ============================================================================
# BASE SCHEMAS & MIXINS (EXISTING)
# ============================================================================

class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""
    created_at: datetime
    updated_at: datetime

class ProgressMixin(BaseModel):
    """Mixin for progress tracking"""
    progress_percentage: Decimal = 0.0
    is_completed: bool = False
    completed_at: Optional[datetime] = None

# ============================================================================
# EXISTING SCHEMAS (TOPIC & PDF - COMPLETED)
# ============================================================================

class TopicBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: str = Field(default="#3498db", pattern=r"^#[0-9A-Fa-f]{6}$")

class TopicCreate(TopicBase):
    pass

class TopicUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

class TopicResponse(TopicBase, TimestampMixin):
    id: UUID
    user_id: UUID
    total_pdfs: int = 0
    total_exercises: int = 0
    total_pages: int = 0
    study_progress: Decimal = 0.0
    estimated_completion_hours: int = 0
    last_studied_at: Optional[datetime] = None
    total_study_time: int = 0
    view_count: int = 0
    last_viewed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TopicWithStats(TopicResponse):
    """Topic with calculated statistics"""
    statistics: Dict[str, Any] = {}

# PDF Schemas (existing - keeping for reference)
class PDFBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    pdf_type: str = Field(default="study", pattern=r"^(study|exercise|reference)$")
    difficulty_rating: int = Field(default=1, ge=1, le=5)

class PDFCreate(PDFBase):
    topic_id: UUID
    parent_pdf_id: Optional[UUID] = None
    
class PDFUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    pdf_type: Optional[str] = Field(None, pattern=r"^(study|exercise|reference)$")
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5)
    current_page: Optional[int] = Field(None, ge=1)

class PDFResponse(PDFBase, TimestampMixin, ProgressMixin):
    id: UUID
    user_id: UUID
    topic_id: UUID
    file_name: str
    file_size: int
    total_pages: int = 0
    current_page: int = 1
    upload_status: str
    processing_status: str
    mime_type: str
    parent_pdf_id: Optional[UUID] = None
    reading_position: Dict[str, Any] = {}
    bookmarks: List[Dict[str, Any]] = []
    notes_count: int = 0
    highlights_count: int = 0
    estimated_read_time: int = 0
    actual_read_time: int = 0
    view_count: int = 0
    last_viewed_at: Optional[datetime] = None
    file_size_mb: Optional[float] = None
    reading_progress_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True

# ============================================================================
# TIMER & ANALYTICS SCHEMAS (STAGE 3.4 - NEW)
# ============================================================================

class StudySessionBase(BaseModel):
    session_type: str = Field(default="study", pattern=r"^(study|exercise|review|pomodoro)$")
    notes: Optional[str] = None

class StudySessionCreate(StudySessionBase):
    pdf_id: UUID
    topic_id: UUID
    planned_cycles: int = Field(default=0, ge=0, le=20)

class StudySessionUpdate(BaseModel):
    session_type: Optional[str] = Field(None, pattern=r"^(study|exercise|review|pomodoro)$")
    notes: Optional[str] = None
    session_rating: Optional[int] = Field(None, ge=1, le=5)

class StudySessionResponse(StudySessionBase, TimestampMixin):
    id: UUID
    user_id: UUID
    pdf_id: UUID
    topic_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    total_minutes: int = 0
    active_minutes: int = 0
    idle_minutes: int = 0
    break_minutes: int = 0
    pages_visited: int = 0
    pages_completed: int = 0
    clicks_count: int = 0
    scroll_events: int = 0
    interruptions: int = 0
    pomodoro_cycles: int = 0
    planned_cycles: int = 0
    focus_score: Decimal = 0.0
    productivity_score: Decimal = 0.0
    comprehension_score: Decimal = 0.0
    xp_earned: int = 0
    achievements_unlocked: List[str] = []
    is_active: bool = True
    is_paused: bool = False
    pause_count: int = 0
    session_rating: Optional[int] = None
    
    # Computed properties
    duration_minutes: Optional[int] = None
    efficiency_score: Optional[float] = None
    
    class Config:
        from_attributes = True

class StudySessionWithStats(StudySessionResponse):
    """Study session with detailed statistics"""
    statistics: Dict[str, Any] = {}
    page_times: List[Dict[str, Any]] = []
    pomodoro_cycles: List[Dict[str, Any]] = []

class SessionActivityUpdate(BaseModel):
    """Update session activity metrics"""
    pages_visited: Optional[int] = Field(None, ge=0)
    pages_completed: Optional[int] = Field(None, ge=0)
    clicks_count: Optional[int] = Field(None, ge=0)
    scroll_events: Optional[int] = Field(None, ge=0)
    interruptions: Optional[int] = Field(None, ge=0)

class SessionPauseRequest(BaseModel):
    """Request to pause/resume session"""
    reason: Optional[str] = None

class SessionEndRequest(BaseModel):
    """Request to end session"""
    session_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None

# ============================================================================
# PAGE TIMING SCHEMAS
# ============================================================================

class PageTimeBase(BaseModel):
    page_number: int = Field(..., ge=1)
    estimated_words: int = Field(default=0, ge=0)

class PageTimeCreate(PageTimeBase):
    pdf_id: UUID
    session_id: UUID

class PageTimeUpdate(BaseModel):
    activity_count: Optional[int] = Field(None, ge=0)
    click_count: Optional[int] = Field(None, ge=0)
    scroll_count: Optional[int] = Field(None, ge=0)
    zoom_changes: Optional[int] = Field(None, ge=0)
    notes_created: Optional[int] = Field(None, ge=0)
    highlights_made: Optional[int] = Field(None, ge=0)
    bookmarks_added: Optional[int] = Field(None, ge=0)

class PageTimeResponse(PageTimeBase, TimestampMixin):
    id: UUID
    session_id: UUID
    pdf_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    active_time_seconds: int = 0
    idle_time_seconds: int = 0
    activity_count: int = 0
    click_count: int = 0
    scroll_count: int = 0
    zoom_changes: int = 0
    reading_speed_wpm: Optional[Decimal] = None
    difficulty_rating: int = 1
    comprehension_estimate: Decimal = 0.0
    notes_created: int = 0
    highlights_made: int = 0
    bookmarks_added: int = 0
    scroll_positions: List[Dict[str, Any]] = []
    zoom_levels: List[Dict[str, Any]] = []
    
    # Computed properties
    reading_speed_pages_per_hour: Optional[float] = None
    engagement_score: Optional[float] = None
    
    class Config:
        from_attributes = True

class PageActivityEvent(BaseModel):
    """Real-time page activity event"""
    event_type: str = Field(..., pattern=r"^(click|scroll|zoom|note|highlight|bookmark)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    position: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None

# ============================================================================
# POMODORO SCHEMAS
# ============================================================================

class PomodoroSessionBase(BaseModel):
    cycle_type: str = Field(..., pattern=r"^(work|short_break|long_break)$")
    planned_duration_minutes: int = Field(..., ge=1, le=60)

class PomodoroSessionCreate(PomodoroSessionBase):
    study_session_id: UUID
    cycle_number: int = Field(..., ge=1, le=20)

class PomodoroSessionUpdate(BaseModel):
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)
    interrupted: Optional[bool] = None
    interruptions: Optional[int] = Field(None, ge=0)

class PomodoroSessionResponse(PomodoroSessionBase, TimestampMixin):
    id: UUID
    study_session_id: UUID
    cycle_number: int
    actual_duration_minutes: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    completed: bool = False
    interrupted: bool = False
    interruptions: int = 0
    effectiveness_rating: Optional[int] = None
    productivity_score: Decimal = 0.0
    focus_score: Decimal = 0.0
    xp_earned: int = 0
    
    # Computed properties
    completion_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True

class PomodoroSettings(BaseModel):
    """User Pomodoro preferences"""
    work_duration: int = Field(default=25, ge=5, le=60)
    short_break_duration: int = Field(default=5, ge=1, le=30)
    long_break_duration: int = Field(default=15, ge=5, le=60)
    cycles_before_long_break: int = Field(default=4, ge=2, le=10)
    auto_start_breaks: bool = True
    auto_start_cycles: bool = False
    sound_enabled: bool = True
    notifications_enabled: bool = True

# ============================================================================
# READING SPEED & ANALYTICS SCHEMAS
# ============================================================================

class ReadingSpeedBase(BaseModel):
    pages_per_minute: Decimal = Field(..., ge=0, le=10)
    words_per_minute: Decimal = Field(..., ge=0, le=2000)
    content_type: str = Field(default="mixed", pattern=r"^(text|math|diagram|mixed)$")
    difficulty_level: int = Field(default=1, ge=1, le=5)

class ReadingSpeedCreate(ReadingSpeedBase):
    pdf_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    estimated_words: int = Field(default=0, ge=0)
    session_duration: int = Field(..., ge=1)  # Minutes
    environmental_factors: Dict[str, Any] = {}

class ReadingSpeedResponse(ReadingSpeedBase, TimestampMixin):
    id: UUID
    user_id: UUID
    pdf_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    characters_per_minute: Decimal = 0.0
    estimated_words: int = 0
    time_of_day: int
    day_of_week: int
    session_duration: int
    environmental_factors: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True

class TimeEstimateBase(BaseModel):
    estimate_type: str = Field(..., pattern=r"^(completion|session|daily_target|page)$")
    estimated_minutes: int = Field(..., ge=1, le=10080)  # Up to 1 week
    confidence_level: str = Field(default="medium", pattern=r"^(low|medium|high)$")

class TimeEstimateCreate(TimeEstimateBase):
    pdf_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    estimated_sessions: int = Field(default=1, ge=1, le=100)
    factors_used: Dict[str, Any] = {}

class TimeEstimateResponse(TimeEstimateBase, TimestampMixin):
    id: UUID
    user_id: UUID
    pdf_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    estimated_sessions: int = 1
    confidence_score: Decimal = 0.5
    accuracy_score: Optional[Decimal] = None
    based_on_sessions: int = 0
    based_on_pages: int = 0
    factors_used: Dict[str, Any] = {}
    valid_until: Optional[datetime] = None
    is_active: bool = True
    actual_minutes: Optional[int] = None
    variance_percentage: Optional[Decimal] = None
    
    # Computed properties
    estimated_hours: Optional[float] = None
    is_expired: Optional[bool] = None
    
    class Config:
        from_attributes = True

class UserStatisticBase(BaseModel):
    stat_type: str = Field(..., pattern=r"^(daily|weekly|monthly|lifetime)$")
    stat_date: datetime

class UserStatisticResponse(UserStatisticBase, TimestampMixin):
    id: UUID
    user_id: UUID
    total_study_minutes: int = 0
    total_active_minutes: int = 0
    total_sessions: int = 0
    pages_read: int = 0
    average_focus_score: Decimal = 0.0
    average_productivity_score: Decimal = 0.0
    average_reading_speed: Decimal = 0.0
    notes_created: int = 0
    highlights_made: int = 0
    bookmarks_added: int = 0
    exercises_completed: int = 0
    study_streak: int = 0
    consistency_score: Decimal = 0.0
    pomodoro_cycles_completed: int = 0
    pomodoro_success_rate: Decimal = 0.0
    xp_earned: int = 0
    level_achieved: int = 1
    achievements_unlocked: List[str] = []
    
    # Computed properties
    efficiency_score: Optional[float] = None
    daily_average_minutes: Optional[float] = None
    
    class Config:
        from_attributes = True

# ============================================================================
# ANALYTICS & INSIGHTS SCHEMAS
# ============================================================================

class StudyAnalyticsRequest(BaseModel):
    """Request for study analytics"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    topic_ids: Optional[List[UUID]] = None
    pdf_ids: Optional[List[UUID]] = None
    granularity: str = Field(default="daily", pattern=r"^(hourly|daily|weekly|monthly)$")

class StudyAnalyticsResponse(BaseModel):
    """Comprehensive study analytics"""
    period: Dict[str, Any]
    overview: Dict[str, Any]
    trends: List[Dict[str, Any]]
    performance: Dict[str, Any]
    reading_speed: Dict[str, Any]
    focus_patterns: Dict[str, Any]
    recommendations: List[str]
    achievements: List[Dict[str, Any]]

class ReadingPatternsResponse(BaseModel):
    """Reading patterns analysis"""
    optimal_study_hours: List[int]
    best_performing_days: List[int]
    reading_speed_trends: List[Dict[str, Any]]
    focus_score_trends: List[Dict[str, Any]]
    productivity_trends: List[Dict[str, Any]]
    content_type_preferences: Dict[str, Any]
    difficulty_performance: Dict[str, Any]

class TimeEstimationAccuracy(BaseModel):
    """Time estimation accuracy analysis"""
    overall_accuracy: Decimal
    accuracy_by_type: Dict[str, Decimal]
    variance_trends: List[Dict[str, Any]]
    improvement_suggestions: List[str]

class FocusAnalytics(BaseModel):
    """Focus and attention analytics"""
    average_focus_score: Decimal
    focus_trends: List[Dict[str, Any]]
    distraction_patterns: Dict[str, Any]
    optimal_session_length: int
    interruption_analysis: Dict[str, Any]
    improvement_recommendations: List[str]

# ============================================================================
# EXISTING UTILITY SCHEMAS
# ============================================================================

class SearchRequest(BaseModel):
    """Generic search request"""
    query: str = Field(..., min_length=1, max_length=255)
    filters: Dict[str, Any] = {}
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)

class SearchResponse(BaseModel):
    """Generic search response"""
    query: str
    total_results: int
    results: List[Dict[str, Any]]
    filters_applied: Dict[str, Any]
    search_time_ms: float

class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Number of items to return")

class BatchDeleteRequest(BaseModel):
    """Request for batch delete operations"""
    ids: List[UUID] = Field(..., min_items=1, max_items=100)
    confirm: bool = Field(..., description="Must be true to confirm batch delete")

class BatchDeleteResponse(BaseModel):
    """Response for batch delete operations"""
    deleted_count: int
    failed_count: int
    failed_ids: List[UUID] = []
    message: str

class BatchUpdateRequest(BaseModel):
    """Request for batch update operations"""
    ids: List[UUID] = Field(..., min_items=1, max_items=100)
    updates: Dict[str, Any] = Field(..., min_items=1)

class BatchUpdateResponse(BaseModel):
    """Response for batch update operations"""
    updated_count: int
    failed_count: int
    failed_ids: List[UUID] = []
    message: str

class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "2.0.0"
    database: str = "connected"
    services: Dict[str, str] = {}

# ============================================================================
# REAL-TIME UPDATES SCHEMAS
# ============================================================================

class SessionUpdateEvent(BaseModel):
    """Real-time session update event"""
    event_type: str = Field(..., pattern=r"^(start|pause|resume|end|activity|page_change)$")
    session_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = {}

class TimerUpdateEvent(BaseModel):
    """Real-time timer update event"""
    event_type: str = Field(..., pattern=r"^(tick|pause|resume|complete|interrupt)$")
    timer_type: str = Field(..., pattern=r"^(session|pomodoro|page)$")
    timer_id: UUID
    current_seconds: int
    total_seconds: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProgressUpdateEvent(BaseModel):
    """Real-time progress update event"""
    event_type: str = Field(..., pattern=r"^(page_complete|exercise_complete|milestone_reached)$")
    user_id: UUID
    progress_data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)