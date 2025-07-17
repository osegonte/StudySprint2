"""
Pydantic schemas package
"""

# Import all schemas here for easy access
from .user import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    UserLogin, 
    UserAuth, 
    TokenResponse,
    UserPreferencesUpdate, 
    UserPreferencesResponse,
    UserSessionResponse
)

__all__ = [
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserLogin",
    "UserAuth",
    "TokenResponse",
    "UserPreferencesUpdate",
    "UserPreferencesResponse", 
    "UserSessionResponse",
]
