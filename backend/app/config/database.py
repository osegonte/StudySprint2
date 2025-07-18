"""Database configuration - Simple version"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Create engine
try:
    engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    logger.info("✅ Database engine created")
except Exception as e:
    logger.error(f"❌ Database engine creation failed: {e}")
    engine = None

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    if engine is None:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_db_connection():
    """Test database connection"""
    if engine is None:
        logger.error("❌ Database engine not created")
        return False
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def init_db():
    """Initialize database tables"""
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created")
    else:
        logger.error("❌ Cannot create tables - no database engine")

async def close_db():
    """Close database connections"""
    if engine is not None:
        engine.dispose()
        logger.info("✅ Database connections closed")
