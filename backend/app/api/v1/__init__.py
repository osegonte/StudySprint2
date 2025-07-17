"""API v1 routes"""

from fastapi import APIRouter
from .auth import router as auth_router

api_router = APIRouter()

# Include auth routes
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
