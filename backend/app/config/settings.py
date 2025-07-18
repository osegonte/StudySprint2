"""
StudySprint 2.0 Settings Configuration
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app settings
    DEBUG: bool = Field(default=True, description="Debug mode")
    SECRET_KEY: str = Field(default="your-secret-key-change-this", description="Secret key for JWT")
    PROJECT_NAME: str = Field(default="StudySprint 2.0", description="Project name")
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql://studysprint:password@localhost:5433/studysprint2",
        description="Database connection URL"
    )
    
    # Redis settings
    REDIS_URL: str = Field(
        default="redis://localhost:6380/0",
        description="Redis connection URL"
    )
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Allowed hosts"
    )
    
    # File storage settings
    UPLOAD_DIR: str = Field(default="storage/uploads", description="Upload directory")
    MAX_FILE_SIZE: int = Field(default=104857600, description="Max file size 100MB")
    
    # JWT settings
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRE_MINUTES: int = Field(default=10080, description="JWT expiration 7 days")
    
    # Email settings (for future use)
    SMTP_HOST: str = Field(default="", description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USER: str = Field(default="", description="SMTP user")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password")
    
    class Config:
        # Don't read from .env file to avoid parsing issues
        env_file = None
        case_sensitive = True
        
    def __init__(self, **kwargs):
        # Remove problematic environment variables before initialization
        problematic_vars = ['MAX_FILE_SIZE', 'JWT_EXPIRE_MINUTES']
        for var in problematic_vars:
            if var in os.environ:
                del os.environ[var]
        super().__init__(**kwargs)


# Global settings instance
settings = Settings()
