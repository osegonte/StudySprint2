# backend/app/api/v1/__init__.py
"""Updated API v1 routes with PDFs"""

from fastapi import APIRouter
from .auth import router as auth_router
from .topics import router as topics_router
from .pdfs import router as pdfs_router

api_router = APIRouter()

# Include all domain routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(topics_router, prefix="/topics", tags=["topics"])
api_router.include_router(pdfs_router, prefix="/pdfs", tags=["pdfs"])