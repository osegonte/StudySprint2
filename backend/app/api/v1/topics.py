# backend/app/api/v1/topics.py
"""Topic Management API Endpoints - Ultra-efficient with CRUD router"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.config.database import get_db
from app.api.v1.auth import get_current_user
from app.services.topic_service import topic_service
from app.models import Topic
from app.schemas import (
    TopicCreate, TopicUpdate, TopicResponse, TopicWithStats,
    SearchRequest, SearchResponse, PaginationParams
)
from app.utils.crud_router import create_user_owned_crud_router
from studysprint_db.models.user import User

# Create base CRUD router
base_router = create_user_owned_crud_router(
    model=Topic,
    create_schema=TopicCreate,
    update_schema=TopicUpdate,
    response_schema=TopicResponse,
    name="topics",
    service_class=type(topic_service)
)

# Create main router and include base routes
router = APIRouter()
router.include_router(base_router)

# ============================================================================
# ENHANCED TOPIC ENDPOINTS
# ============================================================================

@router.get("/with-stats", response_model=List[TopicWithStats])
async def get_topics_with_stats(
    skip: int = Query(0, ge=0, description="Number of topics to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of topics to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all topics with comprehensive statistics"""
    try:
        topics_with_stats = topic_service.get_topics_with_stats(
            db=db, 
            user_id=str(current_user.id), 
            skip=skip, 
            limit=limit
        )
        
        results = []
        for item in topics_with_stats:
            topic_response = TopicResponse.from_orm(item["topic"])
            results.append(TopicWithStats(
                **topic_response.dict(),
                statistics=item["statistics"]
            ))
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get topics with stats: {str(e)}"
        )

@router.get("/{topic_id}/stats", response_model=TopicWithStats)
async def get_topic_stats(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific topic"""
    try:
        topic_data = topic_service.get_topic_with_stats(
            db=db,
            topic_id=topic_id,
            user_id=str(current_user.id)
        )
        
        if not topic_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
        topic_response = TopicResponse.from_orm(topic_data["topic"])
        return TopicWithStats(
            **topic_response.dict(),
            statistics=topic_data["statistics"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get topic stats: {str(e)}"
        )

@router.get("/{topic_id}/analytics")
async def get_topic_analytics(
    topic_id: UUID,
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics for a topic"""
    try:
        analytics = topic_service.get_topic_analytics(
            db=db,
            topic_id=topic_id,
            user_id=str(current_user.id),
            days=days
        )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get topic analytics: {str(e)}"
        )

@router.get("/popular", response_model=List[TopicResponse])
async def get_popular_topics(
    limit: int = Query(10, ge=1, le=50, description="Number of popular topics to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get most studied topics by total study time"""
    try:
        topics = topic_service.get_popular_topics(
            db=db,
            user_id=str(current_user.id),
            limit=limit
        )
        
        return [TopicResponse.from_orm(topic) for topic in topics]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular topics: {str(e)}"
        )

@router.post("/search", response_model=SearchResponse)
async def search_topics(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search topics by name and description"""
    try:
        import time
        start_time = time.time()
        
        topics = topic_service.search_topics(
            db=db,
            user_id=str(current_user.id),
            query=search_request.query,
            limit=search_request.limit
        )
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        results = [TopicResponse.from_orm(topic).dict() for topic in topics]
        
        return SearchResponse(
            query=search_request.query,
            total_results=len(results),
            results=results,
            filters_applied=search_request.filters,
            search_time_ms=round(search_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.post("/{topic_id}/duplicate", response_model=TopicResponse)
async def duplicate_topic(
    topic_id: UUID,
    new_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate an existing topic"""
    try:
        duplicate = topic_service.duplicate_topic(
            db=db,
            topic_id=topic_id,
            user_id=str(current_user.id),
            new_name=new_name
        )
        
        return TopicResponse.from_orm(duplicate)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate topic: {str(e)}"
        )

@router.delete("/{topic_id}/force")
async def force_delete_topic(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Force delete topic and all associated PDFs"""
    try:
        success = topic_service.delete_topic(
            db=db,
            topic_id=topic_id,
            user_id=str(current_user.id),
            force=True
        )
        
        if success:
            return {"message": "Topic and all associated data deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to force delete topic: {str(e)}"
        )

@router.post("/{topic_id}/refresh-stats")
async def refresh_topic_stats(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually refresh topic statistics"""
    try:
        # Verify topic exists and user owns it
        topic = topic_service.get(db, id=topic_id, user_id=str(current_user.id))
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
        # Refresh statistics
        topic_service._refresh_topic_statistics(db, topic_id)
        
        return {"message": "Topic statistics refreshed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh stats: {str(e)}"
        )

# ============================================================================
# TOPIC ORGANIZATION ENDPOINTS
# ============================================================================

@router.put("/reorder")
async def reorder_topics(
    topic_ids: List[UUID],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder topics by updating their display order"""
    try:
        # Verify all topics belong to user
        topics = []
        for topic_id in topic_ids:
            topic = topic_service.get(db, id=topic_id, user_id=str(current_user.id))
            if not topic:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Topic {topic_id} not found"
                )
            topics.append(topic)
        
        # Update display order (using metadata for now)
        for index, topic in enumerate(topics):
            if not topic.metadata:
                topic.metadata = {}
            topic.metadata["display_order"] = index
        
        db.commit()
        
        return {"message": f"Reordered {len(topics)} topics successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder topics: {str(e)}"
        )

@router.get("/colors/suggestions")
async def get_color_suggestions():
    """Get suggested colors for topics"""
    return {
        "primary_colors": [
            "#3498db",  # Blue
            "#e74c3c",  # Red
            "#2ecc71",  # Green
            "#f39c12",  # Orange
            "#9b59b6",  # Purple
            "#1abc9c",  # Turquoise
            "#e67e22",  # Carrot
            "#34495e",  # Dark Blue Gray
        ],
        "pastel_colors": [
            "#74b9ff",  # Light Blue
            "#fd79a8",  # Light Pink
            "#fdcb6e",  # Light Orange
            "#6c5ce7",  # Light Purple
            "#55a3ff",  # Sky Blue
            "#fd79a8",  # Rose
            "#a29bfe",  # Lavender
            "#ffeaa7",  # Light Yellow
        ],
        "dark_colors": [
            "#2d3436",  # Dark Gray
            "#636e72",  # Medium Gray
            "#2c3e50",  # Dark Blue
            "#27ae60",  # Dark Green
            "#8e44ad",  # Dark Purple
            "#d63031",  # Dark Red
            "#e17055",  # Dark Orange
            "#00b894",  # Dark Teal
        ]
    }

# ============================================================================
# BULK OPERATIONS
# ============================================================================

from app.schemas import BatchDeleteRequest, BatchDeleteResponse, BatchUpdateRequest, BatchUpdateResponse

@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_topics(
    batch_request: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete multiple topics in batch"""
    if not batch_request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm batch delete operation"
        )
    
    try:
        deleted_count = 0
        failed_count = 0
        failed_ids = []
        
        for topic_id in batch_request.ids:
            try:
                success = topic_service.delete_topic(
                    db=db,
                    topic_id=topic_id,
                    user_id=str(current_user.id),
                    force=False
                )
                if success:
                    deleted_count += 1
                else:
                    failed_count += 1
                    failed_ids.append(topic_id)
            except Exception:
                failed_count += 1
                failed_ids.append(topic_id)
        
        return BatchDeleteResponse(
            deleted_count=deleted_count,
            failed_count=failed_count,
            failed_ids=failed_ids,
            message=f"Deleted {deleted_count} topics, {failed_count} failed"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch delete failed: {str(e)}"
        )

@router.put("/batch-update", response_model=BatchUpdateResponse)
async def batch_update_topics(
    batch_request: BatchUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update multiple topics in batch"""
    try:
        updated_count = 0
        failed_count = 0
        failed_ids = []
        
        # Validate update fields
        allowed_fields = {"color", "description"}
        update_fields = set(batch_request.updates.keys())
        
        if not update_fields.issubset(allowed_fields):
            invalid_fields = update_fields - allowed_fields
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid update fields: {invalid_fields}. Allowed: {allowed_fields}"
            )
        
        for topic_id in batch_request.ids:
            try:
                topic = topic_service.get(db, id=topic_id, user_id=str(current_user.id))
                if topic:
                    # Apply updates
                    for field, value in batch_request.updates.items():
                        if hasattr(topic, field):
                            setattr(topic, field, value)
                    updated_count += 1
                else:
                    failed_count += 1
                    failed_ids.append(topic_id)
            except Exception:
                failed_count += 1
                failed_ids.append(topic_id)
        
        if updated_count > 0:
            db.commit()
        
        return BatchUpdateResponse(
            updated_count=updated_count,
            failed_count=failed_count,
            failed_ids=failed_ids,
            message=f"Updated {updated_count} topics, {failed_count} failed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch update failed: {str(e)}"
        )