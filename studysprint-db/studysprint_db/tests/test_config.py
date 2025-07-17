"""Tests for database configuration"""

import pytest
from sqlalchemy import create_engine
from studysprint_db.config.database import Base, create_database_engine, BaseModel
from studysprint_db.config.settings import DatabaseSettings

def test_database_settings():
    """Test database settings loading"""
    settings = DatabaseSettings()
    
    assert settings.DATABASE_URL is not None
    assert settings.DB_POOL_SIZE > 0
    assert isinstance(settings.DEBUG, bool)

def test_engine_creation():
    """Test database engine creation"""
    # Use SQLite for testing
    test_url = "sqlite:///:memory:"
    
    engine = create_database_engine(test_url)
    assert engine is not None
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        assert result.fetchone()[0] == 1

def test_base_model():
    """Test base model functionality"""
    # This is a basic structure test
    assert hasattr(BaseModel, 'id')
    assert hasattr(BaseModel, 'created_at')
    assert hasattr(BaseModel, 'updated_at')
    assert hasattr(BaseModel, 'is_deleted')

if __name__ == "__main__":
    pytest.main([__file__])
