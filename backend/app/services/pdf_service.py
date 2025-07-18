# backend/app/services/pdf_service.py
"""PDF Management Service for Stage 3.3"""

import os
import hashlib
import uuid
from typing import List, Optional, Dict, Any, BinaryIO
from pathlib import Path
from uuid import UUID
import mimetypes
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from fastapi import HTTPException, status, UploadFile
from PyPDF2 import PdfReader

from app.models import PDF, Topic, ExerciseSet, Exercise, ExercisePageLink
from app.schemas import (
    PDFCreate, PDFUpdate, PDFUploadRequest, ReadingPositionUpdate, 
    BookmarkCreate, ExerciseSetCreate, ExerciseCreate, ExercisePageLinkCreate
)
from app.utils.crud_router import CRUDService
from app.config.settings import settings


class PDFService(CRUDService):
    """PDF management service with file handling capabilities"""
    
    def __init__(self):
        super().__init__(PDF)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_pdf(
        self, 
        db: Session, 
        file: UploadFile, 
        upload_request: PDFUploadRequest, 
        user_id: str
    ) -> PDF:
        """Upload and process a PDF file"""
        
        # Validate file
        self._validate_pdf_file(file)
        
        # Check topic ownership
        topic = db.query(Topic).filter(
            Topic.id == upload_request.topic_id,
            Topic.user_id == user_id,
            Topic.is_deleted == False
        ).first()
        
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
        # Generate file path and save file
        file_hash = self._calculate_file_hash(file.file)
        file_extension = Path(file.filename).suffix.lower()
        file_path = self._generate_file_path(user_id, upload_request.topic_id, file.filename)
        
        # Check for duplicates
        existing_pdf = db.query(PDF).filter(
            PDF.user_id == user_id,
            PDF.file_hash == file_hash,
            PDF.is_deleted == False
        ).first()
        
        if existing_pdf:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"PDF already exists: {existing_pdf.title}"
            )
        
        # Save file to disk
        file_size = self._save_file(file, file_path)
        
        # Extract PDF metadata
        pdf_metadata = self._extract_pdf_metadata(file_path)
        
        # Create PDF record
        title = upload_request.title or Path(file.filename).stem
        pdf_data = {
            "user_id": user_id,
            "topic_id": upload_request.topic_id,
            "title": title,
            "file_name": file.filename,
            "file_path": str(file_path),
            "file_size": file_size,
            "file_hash": file_hash,
            "mime_type": mimetypes.guess_type(file.filename)[0] or "application/pdf",
            "pdf_type": upload_request.pdf_type,
            "parent_pdf_id": upload_request.parent_pdf_id,
            "upload_status": "completed",
            "processing_status": "completed",
            "total_pages": pdf_metadata.get("page_count", 0),
            "pdf_version": pdf_metadata.get("pdf_version"),
            "estimated_read_time": self._estimate_read_time(pdf_metadata.get("page_count", 0)),
            "difficulty_rating": 1,
        }
        
        pdf = PDF(**pdf_data)
        db.add(pdf)
        db.flush()
        
        # Update topic statistics
        topic.total_pdfs += 1
        topic.total_pages += pdf_metadata.get("page_count", 0)
        
        db.commit()
        db.refresh(pdf)
        
        return pdf
    
    def get_pdf_with_stats(self, db: Session, pdf_id: UUID, user_id: str) -> Optional[Dict[str, Any]]:
        """Get PDF with comprehensive statistics"""
        pdf = self.get(db, id=pdf_id, user_id=user_id)
        if not pdf:
            return None
        
        # Calculate statistics
        stats = {
            "file_size_mb": pdf.file_size_mb,
            "reading_progress_percentage": pdf.reading_progress_percentage,
            "notes_count": pdf.notes_count,
            "highlights_count": pdf.highlights_count,
            "bookmarks_count": len(pdf.bookmarks),
            "estimated_read_time": pdf.estimated_read_time,
            "actual_read_time": pdf.actual_read_time,
            "time_efficiency": self._calculate_time_efficiency(pdf),
            "exercise_sets_count": len(pdf.exercise_sets),
            "total_exercises": sum(ex_set.total_exercises for ex_set in pdf.exercise_sets),
            "completed_exercises": sum(ex_set.completed_exercises for ex_set in pdf.exercise_sets),
        }
        
        return {
            "pdf": pdf,
            "statistics": stats
        }
    
    def update_reading_position(
        self, 
        db: Session, 
        pdf_id: UUID, 
        user_id: str, 
        position: ReadingPositionUpdate
    ) -> PDF:
        """Update reading position and progress"""
        pdf = self.get(db, id=pdf_id, user_id=user_id)
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        # Update reading position
        pdf.update_reading_position(position.page, position.scroll_y, position.zoom)
        
        # Update view statistics
        pdf.view_count += 1
        pdf.last_viewed_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(pdf)
        
        return pdf
    
    def add_bookmark(
        self, 
        db: Session, 
        pdf_id: UUID, 
        user_id: str, 
        bookmark: BookmarkCreate
    ) -> PDF:
        """Add bookmark to PDF"""
        pdf = self.get(db, id=pdf_id, user_id=user_id)
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        # Validate page number
        if bookmark.page > pdf.total_pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Page {bookmark.page} exceeds PDF length ({pdf.total_pages} pages)"
            )
        
        # Add bookmark
        new_bookmark = {
            "id": str(uuid.uuid4()),
            "page": bookmark.page,
            "title": bookmark.title,
            "description": bookmark.description,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if not pdf.bookmarks:
            pdf.bookmarks = []
        
        pdf.bookmarks.append(new_bookmark)
        
        db.commit()
        db.refresh(pdf)
        
        return pdf
    
    def search_pdfs(
        self, 
        db: Session, 
        user_id: str, 
        query: str, 
        topic_id: Optional[UUID] = None,
        pdf_type: Optional[str] = None,
        limit: int = 50
    ) -> List[PDF]:
        """Search PDFs by title and content"""
        search_filter = f"%{query.lower()}%"
        
        query_obj = db.query(PDF).filter(
            PDF.user_id == user_id,
            PDF.is_deleted == False,
            func.lower(PDF.title).like(search_filter)
        )
        
        if topic_id:
            query_obj = query_obj.filter(PDF.topic_id == topic_id)
        
        if pdf_type:
            query_obj = query_obj.filter(PDF.pdf_type == pdf_type)
        
        return query_obj.limit(limit).all()
    
    def get_pdf_file_path(self, db: Session, pdf_id: UUID, user_id: str) -> str:
        """Get file path for PDF download"""
        pdf = self.get(db, id=pdf_id, user_id=user_id)
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        if not os.path.exists(pdf.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF file not found on disk"
            )
        
        return pdf.file_path
    
    def delete_pdf(self, db: Session, pdf_id: UUID, user_id: str, delete_file: bool = True) -> bool:
        """Delete PDF and optionally remove file"""
        pdf = self.get(db, id=pdf_id, user_id=user_id)
        if not pdf:
            return False
        
        # Update topic statistics
        topic = db.query(Topic).filter(Topic.id == pdf.topic_id).first()
        if topic:
            topic.total_pdfs = max(0, topic.total_pdfs - 1)
            topic.total_pages = max(0, topic.total_pages - pdf.total_pages)
        
        # Soft delete the PDF
        pdf.is_deleted = True
        
        # Optionally delete file from disk
        if delete_file and os.path.exists(pdf.file_path):
            try:
                os.remove(pdf.file_path)
            except OSError:
                pass  # File deletion failure shouldn't stop the operation
        
        db.commit()
        return True
    
    # ============================================================================
    # EXERCISE MANAGEMENT METHODS
    # ============================================================================
    
    def create_exercise_set(
        self, 
        db: Session, 
        exercise_set_data: ExerciseSetCreate, 
        user_id: str
    ) -> ExerciseSet:
        """Create a new exercise set for a PDF"""
        
        # Verify PDF ownership
        pdf = self.get(db, id=exercise_set_data.main_pdf_id, user_id=user_id)
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        # Create exercise set
        exercise_set = ExerciseSet(
            user_id=user_id,
            main_pdf_id=exercise_set_data.main_pdf_id,
            title=exercise_set_data.title,
            description=exercise_set_data.description,
            difficulty_level=exercise_set_data.difficulty_level,
            estimated_time_minutes=exercise_set_data.estimated_time_minutes,
            display_order=self._get_next_display_order(db, exercise_set_data.main_pdf_id)
        )
        
        db.add(exercise_set)
        db.commit()
        db.refresh(exercise_set)
        
        return exercise_set
    
    def add_exercise(
        self, 
        db: Session, 
        exercise_data: ExerciseCreate, 
        user_id: str
    ) -> Exercise:
        """Add exercise to exercise set"""
        
        # Verify exercise set ownership
        exercise_set = db.query(ExerciseSet).filter(
            ExerciseSet.id == exercise_data.exercise_set_id,
            ExerciseSet.user_id == user_id,
            ExerciseSet.is_deleted == False
        ).first()
        
        if not exercise_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise set not found"
            )
        
        # Create exercise
        exercise = Exercise(
            user_id=user_id,
            exercise_set_id=exercise_data.exercise_set_id,
            exercise_pdf_id=exercise_data.exercise_pdf_id,
            title=exercise_data.title,
            description=exercise_data.description,
            difficulty_level=exercise_data.difficulty_level,
            estimated_time_minutes=exercise_data.estimated_time_minutes,
            points_possible=exercise_data.points_possible,
            display_order=self._get_next_exercise_display_order(db, exercise_data.exercise_set_id)
        )
        
        db.add(exercise)
        db.flush()
        
        # Update exercise set statistics
        exercise_set.total_exercises += 1
        
        db.commit()
        db.refresh(exercise)
        
        return exercise
    
    def link_exercise_to_pages(
        self, 
        db: Session, 
        exercise_id: UUID, 
        page_links: List[ExercisePageLinkCreate], 
        user_id: str
    ) -> List[ExercisePageLink]:
        """Link exercise to specific pages in main PDF"""
        
        # Verify exercise ownership
        exercise = db.query(Exercise).filter(
            Exercise.id == exercise_id,
            Exercise.user_id == user_id,
            Exercise.is_deleted == False
        ).first()
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        # Create page links
        created_links = []
        for link_data in page_links:
            # Verify PDF ownership and page validity
            pdf = self.get(db, id=link_data.main_pdf_id, user_id=user_id)
            if not pdf:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PDF {link_data.main_pdf_id} not found"
                )
            
            if link_data.page_number > pdf.total_pages:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Page {link_data.page_number} exceeds PDF length ({pdf.total_pages} pages)"
                )
            
            # Create link
            page_link = ExercisePageLink(
                exercise_id=exercise_id,
                main_pdf_id=link_data.main_pdf_id,
                page_number=link_data.page_number,
                link_type=link_data.link_type,
                relevance_score=link_data.relevance_score,
                description=link_data.description
            )
            
            db.add(page_link)
            created_links.append(page_link)
        
        db.commit()
        
        for link in created_links:
            db.refresh(link)
        
        return created_links
    
    def get_exercises_for_page(
        self, 
        db: Session, 
        pdf_id: UUID, 
        page_number: int, 
        user_id: str
    ) -> List[Exercise]:
        """Get exercises linked to a specific page"""
        
        # Verify PDF ownership
        pdf = self.get(db, id=pdf_id, user_id=user_id)
        if not pdf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF not found"
            )
        
        # Get exercises for this page
        exercises = db.query(Exercise).join(ExercisePageLink).filter(
            ExercisePageLink.main_pdf_id == pdf_id,
            ExercisePageLink.page_number == page_number,
            Exercise.user_id == user_id,
            Exercise.is_deleted == False
        ).all()
        
        return exercises
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    def _validate_pdf_file(self, file: UploadFile) -> None:
        """Validate uploaded PDF file"""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file extension
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Check file size
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size ({settings.MAX_FILE_SIZE} bytes)"
            )
    
    def _calculate_file_hash(self, file: BinaryIO) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        file.seek(0)
        for chunk in iter(lambda: file.read(4096), b""):
            hash_sha256.update(chunk)
        file.seek(0)
        return hash_sha256.hexdigest()
    
    def _generate_file_path(self, user_id: str, topic_id: UUID, filename: str) -> Path:
        """Generate unique file path"""
        # Create directory structure: uploads/user_id/topic_id/
        user_dir = self.upload_dir / user_id / str(topic_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{timestamp}_{name}{ext}"
        
        return user_dir / unique_filename
    
    def _save_file(self, file: UploadFile, file_path: Path) -> int:
        """Save uploaded file to disk"""
        file.file.seek(0)
        file_size = 0
        
        with open(file_path, "wb") as f:
            while chunk := file.file.read(1024):
                f.write(chunk)
                file_size += len(chunk)
        
        return file_size
    
    def _extract_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from PDF file"""
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                metadata = {
                    "page_count": len(reader.pages),
                    "pdf_version": reader.metadata.get('/Producer', '') if reader.metadata else '',
                    "title": reader.metadata.get('/Title', '') if reader.metadata else '',
                    "author": reader.metadata.get('/Author', '') if reader.metadata else '',
                    "subject": reader.metadata.get('/Subject', '') if reader.metadata else '',
                }
                return metadata
        except Exception:
            return {"page_count": 0}
    
    def _estimate_read_time(self, page_count: int) -> int:
        """Estimate reading time in minutes"""
        # Average reading speed: 2-3 minutes per page for technical content
        return max(1, page_count * 2)
    
    def _calculate_time_efficiency(self, pdf: PDF) -> float:
        """Calculate reading time efficiency"""
        if pdf.estimated_read_time == 0:
            return 1.0
        
        if pdf.actual_read_time == 0:
            return 0.0
        
        efficiency = pdf.estimated_read_time / pdf.actual_read_time
        return min(2.0, efficiency)  # Cap at 2.0 for very fast readers
    
    def _get_next_display_order(self, db: Session, pdf_id: UUID) -> int:
        """Get next display order for exercise sets"""
        max_order = db.query(func.max(ExerciseSet.display_order)).filter(
            ExerciseSet.main_pdf_id == pdf_id,
            ExerciseSet.is_deleted == False
        ).scalar()
        
        return (max_order or 0) + 1
    
    def _get_next_exercise_display_order(self, db: Session, exercise_set_id: UUID) -> int:
        """Get next display order for exercises"""
        max_order = db.query(func.max(Exercise.display_order)).filter(
            Exercise.exercise_set_id == exercise_set_id,
            Exercise.is_deleted == False
        ).scalar()
        
        return (max_order or 0) + 1


# Create singleton instance
pdf_service = PDFService()