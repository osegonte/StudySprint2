"""
SQLAlchemy models package
"""

# Import all models here for easy access and to ensure they're registered with SQLAlchemy
from .user import User, UserSession, UserPreferences

# List all models for easy iteration
__all__ = [
    "User",
    "UserSession", 
    "UserPreferences",
]
