"""StudySprint 2.0 Settings - Final Working Version"""

class Settings:
    """Simple application settings"""
    
    # Basic app settings
    DEBUG = True
    SECRET_KEY = "your-secret-key-change-this"
    PROJECT_NAME = "StudySprint 2.0"
    
    # Database settings - Use default postgres user (this always works)
    DATABASE_URL = "postgresql://postgres:password@127.0.0.1:5432/studysprint2"
    
    # File storage settings
    UPLOAD_DIR = "storage/uploads"
    MAX_FILE_SIZE = 104857600
    
    # JWT settings
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = 10080

# Global settings instance
settings = Settings()
