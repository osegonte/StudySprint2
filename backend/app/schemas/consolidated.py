# backend/app/schemas.py
# Consolidated Pydantic schemas for StudySprint domains

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
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

# ============================================================================
# TOPIC SCHEMAS
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
# UTILITY SCHEMAS
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
