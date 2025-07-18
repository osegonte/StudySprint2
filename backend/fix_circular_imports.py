# backend/fix_circular_imports.py
"""Fix circular import issues in the project"""

def fix_models_init():
    """Fix the models/__init__.py file"""
    models_init_content = '''"""Models package - import from the consolidated models file"""

# Import all models from the consolidated models.py file
from app.models import (
    Topic,
    PDF,
    ExerciseSet,
    Exercise,
    ExercisePageLink,
    StudySession,
    PageTime,
    PomodoroSession,
    Note,
    NoteLink,
    NoteTag,
    Highlight,
    NoteAttachment,
    ReadingSpeed,
    TimeEstimate,
    UserStatistic,
    Goal,
    GoalProgress,
)

__all__ = [
    "Topic",
    "PDF",
    "ExerciseSet", 
    "Exercise",
    "ExercisePageLink",
    "StudySession",
    "PageTime",
    "PomodoroSession",
    "Note",
    "NoteLink",
    "NoteTag",
    "Highlight",
    "NoteAttachment",
    "ReadingSpeed",
    "TimeEstimate",
    "UserStatistic",
    "Goal",
    "GoalProgress",
]
'''
    
    # Actually, the issue is that models/__init__.py is trying to import from app.models
    # But app.models is the directory itself. Let's just make it empty for now
    simple_init = '''"""Models package"""

# For now, import models directly from the consolidated file:
# from app.models import Topic, PDF, etc.
'''
    
    with open('app/models/__init__.py', 'w') as f:
        f.write(simple_init)
    print("✅ Fixed app/models/__init__.py")

def fix_schemas_init():
    """Fix the schemas/__init__.py file"""
    schemas_init_content = '''"""Schemas package"""

# For now, import schemas directly from the consolidated file:
# from app.schemas import TopicCreate, TopicResponse, etc.
'''
    
    with open('app/schemas/__init__.py', 'w') as f:
        f.write(schemas_init_content)
    print("✅ Fixed app/schemas/__init__.py")

def fix_database_config():
    """Fix the database configuration imports"""
    database_config_content = '''"""
Database configuration using studysprint-db package
"""

from sqlalchemy import text
from studysprint_db.config.database import (
    Base, 
    create_database_engine, 
    create_session_factory
)
from studysprint_db.config.settings import db_settings

# Import user models from studysprint-db
from studysprint_db.models.user import User, UserSession, UserPreferences

# Import our models directly (not through __init__.py to avoid circular imports)
# We'll import these as needed in specific files, not globally here

# Create engine and session factory
engine = create_database_engine(db_settings.DATABASE_URL, echo=db_settings.DB_ECHO)
SessionLocal = create_session_factory(engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Initialize database tables"""
    # Import models here to avoid circular imports
    from app.models import Topic
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

async def close_db():
    """Close database connections"""
    engine.dispose()
'''
    
    with open('app/config/database.py', 'w') as f:
        f.write(database_config_content)
    print("✅ Fixed app/config/database.py")

def fix_topic_service():
    """Fix the topic service imports"""
    topic_service_content = '''# backend/app/services/topic_service.py
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
    
    def __init__(self):
        super().__init__(Topic)
    
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
'''
    
    with open('app/services/topic_service.py', 'w') as f:
        f.write(topic_service_content)
    print("✅ Fixed app/services/topic_service.py")

def main():
    """Run all circular import fixes"""
    print("🔧 Fixing circular import issues...")
    
    try:
        fix_models_init()
        fix_schemas_init()
        fix_database_config()
        fix_topic_service()
        
        print("\n✅ All circular import fixes applied!")
        print("Now try: python verify_setup.py")
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()