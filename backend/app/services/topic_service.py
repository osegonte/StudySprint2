# backend/app/services/topic_service.py
"""Minimal Topic Service for Stage 3.2 initial setup"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from uuid import UUID

# Import models and schemas directly to avoid circular imports
from app.models import Topic
from app.schemas import TopicCreate, TopicUpdate
from app.utils.crud_router import CRUDService
from studysprint_db.models.user import User

class TopicService(CRUDService):
    """Basic topic service"""
    
    def __init__(self, model=None):
        # If no model is provided, use Topic by default
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
        """Get topic with basic statistics"""
        topic = self.get(db, id=topic_id, user_id=user_id)
        if not topic:
            return None
        
        # Basic stats for now
        stats = {
            "total_pdfs": topic.total_pdfs,
            "total_pages": topic.total_pages,
            "study_progress": float(topic.study_progress),
            "total_study_time_minutes": topic.total_study_time,
            "last_studied_at": topic.last_studied_at
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
            stats = {
                "total_pdfs": topic.total_pdfs,
                "total_pages": topic.total_pages,
                "study_progress": float(topic.study_progress),
                "total_study_time_minutes": topic.total_study_time,
                "last_studied_at": topic.last_studied_at
            }
            results.append({
                "topic": topic,
                "statistics": stats
            })
        
        return results
    
    def search_topics(self, db: Session, user_id: str, query: str, limit: int = 50) -> List[Topic]:
        """Search topics by name"""
        search_filter = f"%{query.lower()}%"
        
        return db.query(Topic).filter(
            Topic.user_id == user_id,
            Topic.is_deleted == False,
            func.lower(Topic.name).like(search_filter)
        ).limit(limit).all()

# Create singleton instance
topic_service = TopicService()
