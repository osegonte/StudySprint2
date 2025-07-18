"""Schemas package - import from consolidated schemas"""

from .consolidated import (
    TopicCreate,
    TopicUpdate,
    TopicResponse,
    TopicWithStats,
    SearchRequest,
    SearchResponse,
    PaginationParams,
    BatchDeleteRequest,
    BatchDeleteResponse,
    BatchUpdateRequest,
    BatchUpdateResponse,
    SuccessResponse,
    ErrorResponse,
    HealthCheckResponse,
)

__all__ = [
    "TopicCreate",
    "TopicUpdate",
    "TopicResponse", 
    "TopicWithStats",
    "SearchRequest",
    "SearchResponse",
    "PaginationParams",
    "BatchDeleteRequest",
    "BatchDeleteResponse",
    "BatchUpdateRequest",
    "BatchUpdateResponse",
    "SuccessResponse",
    "ErrorResponse",
    "HealthCheckResponse",
]
