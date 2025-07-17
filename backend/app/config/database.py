"""
Database configuration using studysprint-db package
"""

from sqlalchemy import text
from studysprint_db.config.database import (
    Base, 
    create_database_engine, 
    create_session_factory
)
from studysprint_db.config.settings import db_settings

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
    # Import all models to register them
    import studysprint_db.models
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

async def close_db():
    """Close database connections"""
    engine.dispose()
