# backend/app/schemas/consolidated.py
# Updated with PDF schemas for Stage 3.3

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from decimal import Decimal

# ============================================================================
# BASE SCHEMAS & MIXINS
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
# TOPIC SCHEMAS (COMPLETED)
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

# ============================================================================
# PDF SCHEMAS (STAGE 3.3 - NEW)
# ============================================================================

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

class PDFUploadRequest(BaseModel):
    """Schema for PDF upload requests"""
    topic_id: UUID
    title: Optional[str] = None  # If not provided, will use filename
    pdf_type: str = Field(default="study", pattern=r"^(study|exercise|reference)$")
    parent_pdf_id: Optional[UUID] = None
    
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
    
    # Computed properties
    file_size_mb: Optional[float] = None
    reading_progress_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True

class PDFWithStats(PDFResponse):
    """PDF with calculated statistics"""
    statistics: Dict[str, Any] = {}

class PDFListResponse(BaseModel):
    """Response for PDF listing with pagination"""
    pdfs: List[PDFResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

class ReadingPositionUpdate(BaseModel):
    """Schema for updating reading position"""
    page: int = Field(..., ge=1)
    scroll_y: float = Field(default=0.0, ge=0.0)
    zoom: float = Field(default=1.0, gt=0.0, le=5.0)

class BookmarkCreate(BaseModel):
    """Schema for creating bookmarks"""
    page: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

# ============================================================================
# EXERCISE SCHEMAS (STAGE 3.3 - NEW)
# ============================================================================

class ExerciseSetBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    difficulty_level: int = Field(default=1, ge=1, le=5)
    estimated_time_minutes: int = Field(default=60, ge=5, le=480)

class ExerciseSetCreate(ExerciseSetBase):
    main_pdf_id: UUID

class ExerciseSetUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)
    estimated_time_minutes: Optional[int] = Field(None, ge=5, le=480)

class ExerciseSetResponse(ExerciseSetBase, TimestampMixin, ProgressMixin):
    id: UUID
    user_id: UUID
    main_pdf_id: UUID
    total_exercises: int = 0
    completed_exercises: int = 0
    display_order: int = 0
    completion_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True

class ExerciseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    difficulty_level: int = Field(default=1, ge=1, le=5)
    estimated_time_minutes: int = Field(default=30, ge=5, le=240)
    points_possible: int = Field(default=100, ge=1, le=1000)

class ExerciseCreate(ExerciseBase):
    exercise_set_id: UUID
    exercise_pdf_id: Optional[UUID] = None

class ExerciseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)
    estimated_time_minutes: Optional[int] = Field(None, ge=5, le=240)
    points_possible: Optional[int] = Field(None, ge=1, le=1000)
    exercise_pdf_id: Optional[UUID] = None
    user_score: Optional[int] = None
    notes: Optional[str] = None

class ExerciseResponse(ExerciseBase, TimestampMixin, ProgressMixin):
    id: UUID
    user_id: UUID
    exercise_set_id: UUID
    exercise_pdf_id: Optional[UUID] = None
    user_score: Optional[int] = None
    completion_date: Optional[datetime] = None
    notes: Optional[str] = None
    display_order: int = 0
    score_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True

class ExercisePageLinkBase(BaseModel):
    page_number: int = Field(..., ge=1)
    link_type: str = Field(default="related", pattern=r"^(related|prerequisite|practice)$")
    relevance_score: Decimal = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = None

class ExercisePageLinkCreate(ExercisePageLinkBase):
    exercise_id: UUID
    main_pdf_id: UUID

class ExercisePageLinkResponse(ExercisePageLinkBase, TimestampMixin):
    id: UUID
    exercise_id: UUID
    main_pdf_id: UUID
    
    class Config:
        from_attributes = True

class ExerciseCompletion(BaseModel):
    """Schema for marking exercise completion"""
    user_score: Optional[int] = Field(None, ge=0, le=1000)
    notes: Optional[str] = None

# ============================================================================
# BULK OPERATIONS SCHEMAS
# ============================================================================

class BulkPDFUpload(BaseModel):
    """Schema for bulk PDF upload"""
    topic_id: UUID
    pdf_type: str = Field(default="study", pattern=r"^(study|exercise|reference)$")
    auto_extract_exercises: bool = False

class FileProcessingStatus(BaseModel):
    """Schema for file processing status"""
    file_name: str
    status: str  # uploading, processing, completed, failed
    progress_percentage: float = 0.0
    error_message: Optional[str] = None
    pdf_id: Optional[UUID] = None

class BulkProcessingResponse(BaseModel):
    """Response for bulk operations"""
    total_files: int
    successful: int
    failed: int
    processing: int
    files: List[FileProcessingStatus]

# ============================================================================
# UTILITY SCHEMAS (EXISTING + NEW)
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