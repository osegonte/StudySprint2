# backend/app/services/topic_service.py
"""Enhanced Topic Service with PDF Integration for Stage 3.3"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.models import Topic, PDF, ExerciseSet, Exercise
from app.schemas import TopicCreate, TopicUpdate
from app.utils.crud_router import CRUDService
from studysprint_db.models.user import User


class TopicService(CRUDService):
    """Enhanced topic service with PDF integration"""
    
    def __init__(self, model=None):
        if model is None:
            model = Topic
        super().__init__(model)
    
    def create_topic(self, db: Session, topic_create: TopicCreate, user_id: str) -> Topic:
        """Create a new topic"""
        # Check for duplicate names
        existing = db.query(Topic).filter(
            Topic.user_id == user_id,
            func.lower(Topic.name) == topic_create.name.lower(),
            Topic.is_deleted == False
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Topic '{topic_create.name}' already exists"
            )
        
        # Create topic
        topic_data = topic_create.dict()
        topic_data["user_id"] = user_id
        
        topic = Topic(**topic_data)
        db.add(topic)
        db.commit()
        db.refresh(topic)
        
        return topic
    
    def get_topic_with_stats(self, db: Session, topic_id: UUID, user_id: str) -> Optional[Dict[str, Any]]:
        """Get topic with comprehensive statistics"""
        topic = self.get(db, id=topic_id, user_id=user_id)
        if not topic:
            return None
        
        # Get PDF statistics
        pdf_stats = db.query(
            func.count(PDF.id).label('total_pdfs'),
            func.sum(PDF.total_pages).label('total_pages'),
            func.sum(PDF.actual_read_time).label('total_study_time'),
            func.avg(PDF.progress_percentage).label('avg_progress')
        ).filter(
            PDF.topic_id == topic_id,
            PDF.user_id == user_id,
            PDF.is_deleted == False
        ).first()
        
        # Get exercise statistics
        exercise_stats = db.query(
            func.count(Exercise.id).label('total_exercises'),
            func.sum(func.case([(Exercise.is_completed == True, 1)], else_=0)).label('completed_exercises')
        ).join(ExerciseSet).join(PDF).filter(
            PDF.topic_id == topic_id,
            PDF.user_id == user_id,
            PDF.is_deleted == False,
            ExerciseSet.is_deleted == False,
            Exercise.is_deleted == False
        ).first()
        
        # Get reading progress
        pages_read = db.query(func.sum(PDF.current_page)).filter(
            PDF.topic_id == topic_id,
            PDF.user_id == user_id,
            PDF.is_deleted == False
        ).scalar() or 0
        
        total_pages = pdf_stats.total_pages or 0
        reading_progress = round((pages_read / total_pages * 100), 2) if total_pages > 0 else 0
        
        # Calculate completion percentage for exercises
        total_exercises = exercise_stats.total_exercises or 0
        completed_exercises = exercise_stats.completed_exercises or 0
        exercise_completion = round((completed_exercises / total_exercises * 100), 2) if total_exercises > 0 else 0
        
        # Get recent activity
        recent_activity = db.query(PDF).filter(
            PDF.topic_id == topic_id,
            PDF.user_id == user_id,
            PDF.is_deleted == False,
            PDF.last_viewed_at.isnot(None)
        ).order_by(desc(PDF.last_viewed_at)).limit(5).all()
        
        stats = {
            "total_pdfs": pdf_stats.total_pdfs or 0,
            "total_pages": total_pages,
            "pages_read": pages_read,
            "reading_progress_percentage": reading_progress,
            "total_study_time_minutes": pdf_stats.total_study_time or 0,
            "average_pdf_progress": round(pdf_stats.avg_progress or 0, 2),
            "total_exercises": total_exercises,
            "completed_exercises": completed_exercises,
            "exercise_completion_percentage": exercise_completion,
            "estimated_completion_time": self._estimate_completion_time(
                total_pages, pages_read, pdf_stats.total_study_time or 0
            ),
            "recent_activity": [
                {
                    "pdf_id": str(pdf.id),
                    "pdf_title": pdf.title,
                    "last_viewed": pdf.last_viewed_at.isoformat() if pdf.last_viewed_at else None,
                    "current_page": pdf.current_page,
                    "total_pages": pdf.total_pages
                }
                for pdf in recent_activity
            ]
        }
        
        return {
            "topic": topic,
            "statistics": stats
        }
    
    def get_topics_with_stats(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all topics with their statistics"""
        topics = self.get_multi(db, user_id=user_id, skip=skip, limit=limit)
        
        results = []
        for topic in topics:
            topic_data = self.get_topic_with_stats(db, topic.id, user_id)
            if topic_data:
                results.append(topic_data)
        
        return results
    
    def get_topic_analytics(self, db: Session, topic_id: UUID, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for a topic"""
        topic = self.get(db, id=topic_id, user_id=user_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
        # Date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Get PDFs in this topic
        pdfs = db.query(PDF).filter(
            PDF.topic_id == topic_id,
            PDF.user_id == user_id,
            PDF.is_deleted == False
        ).all()
        
        # Calculate analytics
        pdf_difficulty_distribution = {}
        pdf_type_distribution = {}
        reading_efficiency = []
        
        for pdf in pdfs:
            # Difficulty distribution
            diff = pdf.difficulty_rating
            pdf_difficulty_distribution[diff] = pdf_difficulty_distribution.get(diff, 0) + 1
            
            # Type distribution
            pdf_type_distribution[pdf.pdf_type] = pdf_type_distribution.get(pdf.pdf_type, 0) + 1
            
            # Reading efficiency
            if pdf.estimated_read_time > 0 and pdf.actual_read_time > 0:
                efficiency = pdf.estimated_read_time / pdf.actual_read_time
                reading_efficiency.append(efficiency)
        
        # Average reading efficiency
        avg_efficiency = sum(reading_efficiency) / len(reading_efficiency) if reading_efficiency else 0
        
        # Study patterns (placeholder - will be enhanced with session data)
        study_patterns = {
            "most_productive_time": "Unknown",
            "average_session_length": 0,
            "consistency_score": 0,
            "focus_score": 0
        }
        
        # Learning insights
        insights = []
        
        if avg_efficiency > 1.2:
            insights.append("You're reading faster than estimated - great progress!")
        elif avg_efficiency < 0.8:
            insights.append("Take your time - understanding is more important than speed")
        
        total_exercises = sum(len(pdf.exercise_sets) for pdf in pdfs)
        if total_exercises == 0:
            insights.append("Consider adding practice exercises to reinforce learning")
        
        return {
            "topic_id": str(topic_id),
            "analysis_period_days": days,
            "total_pdfs": len(pdfs),
            "pdf_difficulty_distribution": pdf_difficulty_distribution,
            "pdf_type_distribution": pdf_type_distribution,
            "reading_efficiency": {
                "average": round(avg_efficiency, 2),
                "samples": len(reading_efficiency)
            },
            "study_patterns": study_patterns,
            "learning_insights": insights,
            "recommendations": self._generate_recommendations(pdfs, avg_efficiency)
        }
    
    def search_topics(self, db: Session, user_id: str, query: str, limit: int = 50) -> List[Topic]:
        """Search topics by name and description"""
        search_filter = f"%{query.lower()}%"
        
        return db.query(Topic).filter(
            Topic.user_id == user_id,
            Topic.is_deleted == False,
            or_(
                func.lower(Topic.name).like(search_filter),
                func.lower(Topic.description).like(search_filter)
            )
        ).limit(limit).all()
    
    def get_popular_topics(self, db: Session, user_id: str, limit: int = 10) -> List[Topic]:
        """Get most studied topics by total study time"""
        return db.query(Topic).filter(
            Topic.user_id == user_id,
            Topic.is_deleted == False
        ).order_by(desc(Topic.total_study_time)).limit(limit).all()
    
    def duplicate_topic(self, db: Session, topic_id: UUID, user_id: str, new_name: Optional[str] = None) -> Topic:
        """Duplicate an existing topic"""
        original = self.get(db, id=topic_id, user_id=user_id)
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found"
            )
        
        # Generate new name
        if not new_name:
            new_name = f"{original.name} (Copy)"
        
        # Ensure name is unique
        counter = 1
        check_name = new_name
        while db.query(Topic).filter(
            Topic.user_id == user_id,
            Topic.name == check_name,
            Topic.is_deleted == False
        ).first():
            check_name = f"{new_name} ({counter})"
            counter += 1
        
        # Create duplicate
        duplicate = Topic(
            user_id=user_id,
            name=check_name,
            description=original.description,
            color=original.color,
            metadata=original.metadata
        )
        
        db.add(duplicate)
        db.commit()
        db.refresh(duplicate)
        
        return duplicate
    
    def delete_topic(self, db: Session, topic_id: UUID, user_id: str, force: bool = False) -> bool:
        """Delete topic and optionally its PDFs"""
        topic = self.get(db, id=topic_id, user_id=user_id)
        if not topic:
            return False
        
        # Check if topic has PDFs
        pdf_count = db.query(func.count(PDF.id)).filter(
            PDF.topic_id == topic_id,
            PDF.is_deleted == False
        ).scalar()
        
        if pdf_count > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Topic contains {pdf_count} PDFs. Use force=True to delete all content."
            )
        
        # If force delete, mark all PDFs as deleted
        if force:
            db.query(PDF).filter(
                PDF.topic_id == topic_id,
                PDF.user_id == user_id
            ).update({"is_deleted": True})
        
        # Delete topic
        topic.is_deleted = True
        db.commit()
        
        return True
    
    def _refresh_topic_statistics(self, db: Session, topic_id: UUID) -> None:
        """Refresh denormalized statistics for a topic"""
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return
        
        # Get current statistics
        stats = db.query(
            func.count(PDF.id).label('total_pdfs'),
            func.sum(PDF.total_pages).label('total_pages'),
            func.sum(PDF.actual_read_time).label('total_study_time'),
            func.max(PDF.last_viewed_at).label('last_studied_at')
        ).filter(
            PDF.topic_id == topic_id,
            PDF.is_deleted == False
        ).first()
        
        # Get exercise count
        exercise_count = db.query(func.count(Exercise.id)).join(ExerciseSet).join(PDF).filter(
            PDF.topic_id == topic_id,
            PDF.is_deleted == False,
            ExerciseSet.is_deleted == False,
            Exercise.is_deleted == False
        ).scalar()
        
        # Update topic statistics
        topic.total_pdfs = stats.total_pdfs or 0
        topic.total_pages = stats.total_pages or 0
        topic.total_study_time = stats.total_study_time or 0
        topic.total_exercises = exercise_count or 0
        topic.last_studied_at = stats.last_studied_at
        
        # Calculate overall progress
        if topic.total_pages > 0:
            pages_read = db.query(func.sum(PDF.current_page)).filter(
                PDF.topic_id == topic_id,
                PDF.is_deleted == False
            ).scalar() or 0
            topic.study_progress = round((pages_read / topic.total_pages * 100), 2)
        
        db.commit()
    
    def _estimate_completion_time(self, total_pages: int, pages_read: int, time_spent: int) -> int:
        """Estimate remaining time to complete topic"""
        if pages_read == 0 or time_spent == 0:
            return total_pages * 2  # Default 2 minutes per page
        
        remaining_pages = total_pages - pages_read
        avg_time_per_page = time_spent / pages_read
        
        return int(remaining_pages * avg_time_per_page)
    
    def _generate_recommendations(self, pdfs: List[PDF], avg_efficiency: float) -> List[str]:
        """Generate study recommendations based on analytics"""
        recommendations = []
        
        # Reading efficiency recommendations
        if avg_efficiency < 0.8:
            recommendations.append("Consider breaking study sessions into smaller chunks")
            recommendations.append("Take notes while reading to improve retention")
        elif avg_efficiency > 1.5:
            recommendations.append("You're reading very quickly - consider adding review sessions")
        
        # Content recommendations
        study_pdfs = [pdf for pdf in pdfs if pdf.pdf_type == 'study']
        exercise_pdfs = [pdf for pdf in pdfs if pdf.pdf_type == 'exercise']
        
        if len(study_pdfs) > 0 and len(exercise_pdfs) == 0:
            recommendations.append("Add practice exercises to reinforce learning")
        
        # Progress recommendations
        stalled_pdfs = [pdf for pdf in pdfs if pdf.current_page == 1 and pdf.total_pages > 1]
        if len(stalled_pdfs) > 2:
            recommendations.append("Focus on completing started PDFs before adding new ones")
        
        # Difficulty recommendations
        high_difficulty = [pdf for pdf in pdfs if pdf.difficulty_rating >= 4]
        if len(high_difficulty) > len(pdfs) * 0.7:
            recommendations.append("Consider adding some easier introductory materials")
        
        return recommendations


# Create singleton instance
topic_service = TopicService()