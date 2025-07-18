# backend/app/api/v1/__init__.py
"""Updated API v1 routes with Topics"""

from fastapi import APIRouter
from .auth import router as auth_router
from .topics import router as topics_router

api_router = APIRouter()

# Include all domain routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(topics_router, prefix="/topics", tags=["topics"])
