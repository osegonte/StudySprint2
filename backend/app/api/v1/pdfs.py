# backend/app/api/v1/pdfs.py
"""PDF Management API Endpoints - Ultra-efficient with CRUD router + File handling"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import os
import mimetypes

from app.config.database import get_db
from app.api.v1.auth import get_current_user
from app.services.pdf_service import pdf_service
from app.models import PDF, ExerciseSet, Exercise
from app.schemas import (
    PDFCreate, PDFUpdate, PDFResponse, PDFWithStats, PDFUploadRequest,
    ReadingPositionUpdate, BookmarkCreate, ExerciseSetCreate, ExerciseSetResponse,
    ExerciseCreate, ExerciseResponse, ExercisePageLinkCreate, ExercisePageLinkResponse,
    SearchRequest, SearchResponse, PaginationParams
)
from app.utils.crud_router import create_user_owned_crud_router
from studysprint_db.models.user import User

# Create base CRUD router for basic PDF operations
base_router = create_user_owned_crud_router(
    model=PDF,
    create_schema=PDFCreate,
    update_schema=PDFUpdate,
    response_schema=PDFResponse,
    name="pdfs",
    service_class=type(pdf_service)
)

# Create main router and include base routes
router = APIRouter()
router.include_router(base_router)

# ============================================================================
# FILE UPLOAD & MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/upload", response_model=PDFResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    topic_id: UUID = Query(..., description="Topic ID to upload PDF to"),
    title: Optional[str] = Query(None, description="PDF title (defaults to filename)"),
    pdf_type: str = Query("study", description="PDF type", regex="^(study|exercise|reference)$"),
    parent_pdf_id: Optional[UUID] = Query(None, description="Parent PDF ID for exercises"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a PDF file"""
    try:
        upload_request = PDFUploadRequest(
            topic_id=topic_id,
            title=title,
            pdf_type=pdf_type,
            parent_pdf_id=parent_pdf_id
        )
        
        pdf = pdf_service.upload_pdf(
            db=db,
            file=file,
            upload_request=upload_request,
            user_id=str(current_user.id)
        )
        
        return PDFResponse.from_orm(pdf)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/download/{pdf_id}")
async def download_pdf(
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download PDF file"""
    try:
        file_path = pdf_service.get_pdf_file_path(db, pdf_id, str(current_user.id))
        
        # Get PDF info for filename
        pdf = pdf_service.get(db, id=pdf_id, user_id=str(current_user.id))
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        # Return file
        return FileResponse(
            path=file_path,
            filename=pdf.file_name,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )

@router.get("/stream/{pdf_id}")
async def stream_pdf(
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream PDF file for in-browser viewing"""
    try:
        file_path = pdf_service.get_pdf_file_path(db, pdf_id, str(current_user.id))
        
        def iter_file():
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    yield chunk
        
        return StreamingResponse(
            iter_file(),
            media_type="application/pdf",
            headers={"Content-Disposition": "inline"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming failed: {str(e)}"
        )

# ============================================================================
# ENHANCED PDF ENDPOINTS
# ============================================================================

@router.get("/with-stats", response_model=List[PDFWithStats])
async def get_pdfs_with_stats(
    topic_id: Optional[UUID] = Query(None, description="Filter by topic ID"),
    pdf_type: Optional[str] = Query(None, description="Filter by PDF type"),
    skip: int = Query(0, ge=0, description="Number of PDFs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of PDFs to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all PDFs with comprehensive statistics"""
    try:
        # Build filters
        filters = {}
        if topic_id:
            filters["topic_id"] = topic_id
        if pdf_type:
            filters["pdf_type"] = pdf_type
        
        pdfs = pdf_service.get_multi(
            db=db,
            user_id=str(current_user.id),
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        results = []
        for pdf in pdfs:
            pdf_data = pdf_service.get_pdf_with_stats(db, pdf.id, str(current_user.id))
            if pdf_data:
                pdf_response = PDFResponse.from_orm(pdf_data["pdf"])
                results.append(PDFWithStats(
                    **pdf_response.dict(),
                    statistics=pdf_data["statistics"]
                ))
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PDFs with stats: {str(e)}"
        )

@router.get("/{pdf_id}/stats", response_model=PDFWithStats)
async def get_pdf_stats(
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a specific PDF"""
    try:
        pdf_data = pdf_service.get_pdf_with_stats(
            db=db,
            pdf_id=pdf_id,
            user_id=str(current_user.id)
        )
        
        if not pdf_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        pdf_response = PDFResponse.from_orm(pdf_data["pdf"])
        return PDFWithStats(
            **pdf_response.dict(),
            statistics=pdf_data["statistics"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PDF stats: {str(e)}"
        )

@router.post("/search", response_model=SearchResponse)
async def search_pdfs(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search PDFs by title and content"""
    try:
        import time
        start_time = time.time()
        
        pdfs = pdf_service.search_pdfs(
            db=db,
            user_id=str(current_user.id),
            query=search_request.query,
            topic_id=search_request.filters.get("topic_id"),
            pdf_type=search_request.filters.get("pdf_type"),
            limit=search_request.limit
        )
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        results = [PDFResponse.from_orm(pdf).dict() for pdf in pdfs]
        
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

# ============================================================================
# READING POSITION & BOOKMARKS
# ============================================================================

@router.put("/{pdf_id}/reading-position", response_model=PDFResponse)
async def update_reading_position(
    pdf_id: UUID,
    position: ReadingPositionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update reading position for a PDF"""
    try:
        pdf = pdf_service.update_reading_position(
            db=db,
            pdf_id=pdf_id,
            user_id=str(current_user.id),
            position=position
        )
        
        return PDFResponse.from_orm(pdf)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update reading position: {str(e)}"
        )

@router.post("/{pdf_id}/bookmarks", response_model=PDFResponse)
async def add_bookmark(
    pdf_id: UUID,
    bookmark: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add bookmark to PDF"""
    try:
        pdf = pdf_service.add_bookmark(
            db=db,
            pdf_id=pdf_id,
            user_id=str(current_user.id),
            bookmark=bookmark
        )
        
        return PDFResponse.from_orm(pdf)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add bookmark: {str(e)}"
        )

@router.get("/{pdf_id}/bookmarks")
async def get_bookmarks(
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bookmarks for a PDF"""
    try:
        pdf = pdf_service.get(db, id=pdf_id, user_id=str(current_user.id))
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        return {"bookmarks": pdf.bookmarks or []}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bookmarks: {str(e)}"
        )

# ============================================================================
# EXERCISE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/{pdf_id}/exercise-sets", response_model=ExerciseSetResponse)
async def create_exercise_set(
    pdf_id: UUID,
    exercise_set_data: ExerciseSetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new exercise set for a PDF"""
    try:
        # Ensure the PDF ID matches
        exercise_set_data.main_pdf_id = pdf_id
        
        exercise_set = pdf_service.create_exercise_set(
            db=db,
            exercise_set_data=exercise_set_data,
            user_id=str(current_user.id)
        )
        
        return ExerciseSetResponse.from_orm(exercise_set)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create exercise set: {str(e)}"
        )

@router.get("/{pdf_id}/exercise-sets", response_model=List[ExerciseSetResponse])
async def get_exercise_sets(
    pdf_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all exercise sets for a PDF"""
    try:
        # Verify PDF ownership
        pdf = pdf_service.get(db, id=pdf_id, user_id=str(current_user.id))
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        exercise_sets = db.query(ExerciseSet).filter(
            ExerciseSet.main_pdf_id == pdf_id,
            ExerciseSet.user_id == current_user.id,
            ExerciseSet.is_deleted == False
        ).order_by(ExerciseSet.display_order).all()
        
        return [ExerciseSetResponse.from_orm(es) for es in exercise_sets]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exercise sets: {str(e)}"
        )

@router.post("/exercise-sets/{set_id}/exercises", response_model=ExerciseResponse)
async def add_exercise(
    set_id: UUID,
    exercise_data: ExerciseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add exercise to exercise set"""
    try:
        # Ensure the exercise set ID matches
        exercise_data.exercise_set_id = set_id
        
        exercise = pdf_service.add_exercise(
            db=db,
            exercise_data=exercise_data,
            user_id=str(current_user.id)
        )
        
        return ExerciseResponse.from_orm(exercise)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add exercise: {str(e)}"
        )

@router.get("/exercise-sets/{set_id}/exercises", response_model=List[ExerciseResponse])
async def get_exercises(
    set_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all exercises in an exercise set"""
    try:
        # Verify exercise set ownership
        exercise_set = db.query(ExerciseSet).filter(
            ExerciseSet.id == set_id,
            ExerciseSet.user_id == current_user.id,
            ExerciseSet.is_deleted == False
        ).first()
        
        if not exercise_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise set not found"
            )
        
        exercises = db.query(Exercise).filter(
            Exercise.exercise_set_id == set_id,
            Exercise.user_id == current_user.id,
            Exercise.is_deleted == False
        ).order_by(Exercise.display_order).all()
        
        return [ExerciseResponse.from_orm(ex) for ex in exercises]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exercises: {str(e)}"
        )

@router.post("/exercises/{exercise_id}/page-links", response_model=List[ExercisePageLinkResponse])
async def link_exercise_to_pages(
    exercise_id: UUID,
    page_links: List[ExercisePageLinkCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Link exercise to specific pages in main PDF"""
    try:
        links = pdf_service.link_exercise_to_pages(
            db=db,
            exercise_id=exercise_id,
            page_links=page_links,
            user_id=str(current_user.id)
        )
        
        return [ExercisePageLinkResponse.from_orm(link) for link in links]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to link exercise to pages: {str(e)}"
        )

@router.get("/{pdf_id}/pages/{page_number}/exercises", response_model=List[ExerciseResponse])
async def get_exercises_for_page(
    pdf_id: UUID,
    page_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get exercises linked to a specific page"""
    try:
        exercises = pdf_service.get_exercises_for_page(
            db=db,
            pdf_id=pdf_id,
            page_number=page_number,
            user_id=str(current_user.id)
        )
        
        return [ExerciseResponse.from_orm(ex) for ex in exercises]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exercises for page: {str(e)}"
        )

@router.put("/exercises/{exercise_id}/complete", response_model=ExerciseResponse)
async def complete_exercise(
    exercise_id: UUID,
    completion_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark exercise as completed"""
    try:
        # Get exercise
        exercise = db.query(Exercise).filter(
            Exercise.id == exercise_id,
            Exercise.user_id == current_user.id,
            Exercise.is_deleted == False
        ).first()
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        # Update completion status
        exercise.is_completed = True
        exercise.completion_date = datetime.now(timezone.utc)
        
        if "user_score" in completion_data:
            exercise.user_score = completion_data["user_score"]
        
        if "notes" in completion_data:
            exercise.notes = completion_data["notes"]
        
        # Update exercise set statistics
        exercise_set = db.query(ExerciseSet).filter(
            ExerciseSet.id == exercise.exercise_set_id
        ).first()
        
        if exercise_set:
            completed_count = db.query(Exercise).filter(
                Exercise.exercise_set_id == exercise.exercise_set_id,
                Exercise.is_completed == True,
                Exercise.is_deleted == False
            ).count()
            
            exercise_set.completed_exercises = completed_count
            
            # Update exercise set completion status
            if completed_count >= exercise_set.total_exercises:
                exercise_set.is_completed = True
                exercise_set.completed_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(exercise)
        
        return ExerciseResponse.from_orm(exercise)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete exercise: {str(e)}"
        )

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.delete("/bulk-delete")
async def bulk_delete_pdfs(
    pdf_ids: List[UUID],
    delete_files: bool = Query(False, description="Delete files from disk"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete multiple PDFs"""
    try:
        deleted_count = 0
        failed_count = 0
        failed_ids = []
        
        for pdf_id in pdf_ids:
            try:
                success = pdf_service.delete_pdf(
                    db=db,
                    pdf_id=pdf_id,
                    user_id=str(current_user.id),
                    delete_file=delete_files
                )
                if success:
                    deleted_count += 1
                else:
                    failed_count += 1
                    failed_ids.append(pdf_id)
            except Exception:
                failed_count += 1
                failed_ids.append(pdf_id)
        
        return {
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "failed_ids": failed_ids,
            "message": f"Deleted {deleted_count} PDFs, {failed_count} failed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk delete failed: {str(e)}"
        )

# ============================================================================
# ANALYTICS & INSIGHTS
# ============================================================================

@router.get("/analytics/reading-stats")
async def get_reading_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days for analytics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reading analytics across all PDFs"""
    try:
        # Get user's PDFs
        pdfs = pdf_service.get_multi(
            db=db,
            user_id=str(current_user.id),
            skip=0,
            limit=1000  # Get all PDFs for analytics
        )
        
        # Calculate analytics
        total_pdfs = len(pdfs)
        total_pages = sum(pdf.total_pages for pdf in pdfs)
        pages_read = sum(pdf.current_page for pdf in pdfs)
        total_study_time = sum(pdf.actual_read_time for pdf in pdfs)
        
        # Calculate average reading speed
        avg_reading_speed = 0
        if total_study_time > 0:
            avg_reading_speed = round(pages_read / (total_study_time / 60), 2)  # pages per hour
        
        # Get PDF type distribution
        pdf_types = {}
        for pdf in pdfs:
            pdf_types[pdf.pdf_type] = pdf_types.get(pdf.pdf_type, 0) + 1
        
        # Get reading progress
        reading_progress = round((pages_read / total_pages * 100), 2) if total_pages > 0 else 0
        
        return {
            "total_pdfs": total_pdfs,
            "total_pages": total_pages,
            "pages_read": pages_read,
            "reading_progress_percentage": reading_progress,
            "total_study_time_minutes": total_study_time,
            "average_reading_speed_pages_per_hour": avg_reading_speed,
            "pdf_type_distribution": pdf_types,
            "most_studied_topics": [],  # Will implement when we have session data
            "reading_trends": []  # Will implement when we have time series data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reading analytics: {str(e)}"
        )

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def pdf_health_check():
    """Health check for PDF service"""
    try:
        # Check upload directory
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir_exists = upload_dir.exists()
        
        # Check if we can write to upload directory
        can_write = os.access(upload_dir, os.W_OK) if upload_dir_exists else False
        
        return {
            "status": "healthy",
            "service": "pdf_management",
            "version": "2.0.0",
            "upload_directory": {
                "path": str(upload_dir),
                "exists": upload_dir_exists,
                "writable": can_write
            },
            "features": [
                "pdf_upload",
                "pdf_download",
                "pdf_streaming",
                "reading_position_tracking",
                "bookmarks",
                "exercise_management",
                "exercise_page_linking",
                "bulk_operations",
                "search",
                "analytics"
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PDF service unhealthy: {str(e)}"
        )