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
        default="postgresql://studysprint:password@localhost:5432/studysprint2",
        description="Database connection URL"
    )
    
    # Redis settings
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
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
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024, description="Max file size (100MB)")
    
    # JWT settings
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, description="JWT expiration (7 days)")
    
    # Email settings (for future use)
    SMTP_HOST: str = Field(default="", description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USER: str = Field(default="", description="SMTP user")
    SMTP_PASSWORD: str = Field(default="", description="SMTP password")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
