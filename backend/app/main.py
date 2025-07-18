"""StudySprint 2.0 - Main FastAPI Application"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.config.database import init_db, close_db, test_db_connection
from app.api.v1 import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 StudySprint 2.0 starting up...")
    
    # Test database connection
    if test_db_connection():
        logger.info("✅ Database connection successful")
        await init_db()
    else:
        logger.warning("⚠️ Database connection failed")
    
    yield
    
    logger.info("📴 StudySprint 2.0 shutting down...")
    await close_db()

# Create FastAPI application
app = FastAPI(
    title="StudySprint 2.0 API",
    description="Advanced PDF Study Management System",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Basic routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StudySprint 2.0 API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "2.0.0"
    }

@app.get("/health/db")
async def database_health():
    """Database health check"""
    if test_db_connection():
        return {
            "database": "connected",
            "status": "healthy"
        }
    else:
        raise HTTPException(status_code=503, detail="Database connection failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
