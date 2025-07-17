"""Database configuration and base classes"""

from sqlalchemy import create_engine, MetaData, Column, DateTime, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class BaseModel:
    """Base model with common fields"""
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

Base = declarative_base(cls=BaseModel)
metadata = MetaData()

def create_database_engine(database_url: str, echo: bool = False, **kwargs):
    """Create database engine with optimal settings"""
    
    default_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10,
        "echo": echo,
    }
    
    engine_kwargs = {**default_kwargs, **kwargs}
    logger.info(f"Creating database engine for: {database_url}")
    
    try:
        engine = create_engine(database_url, **engine_kwargs)
        
        # Test connection with proper SQLAlchemy 2.0 syntax
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
        
        return engine
    
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

def get_table_info(engine):
    """Get information about database tables"""
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    table_info = {}
    for table_name in tables:
        columns = inspector.get_columns(table_name)
        table_info[table_name] = {
            "columns": len(columns),
            "column_names": [col["name"] for col in columns]
        }
    
    return table_info

def create_session_factory(engine):
    """Create session factory"""
    return sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine,
        expire_on_commit=False
    )
