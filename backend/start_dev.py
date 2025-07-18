# backend/start_dev.py
"""Quick development server start script"""

import subprocess
import sys
import os

def start_development_server():
    """Start the development server with all dependencies"""
    
    print("🚀 Starting StudySprint 2.0 Development Server")
    print("=" * 50)
    
    # Check virtual environment
    if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
        print("⚠️  Virtual environment not detected!")
        print("   Run: source venv/bin/activate")
        return
    
    # Check dependencies
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ Dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements-dev.txt")
        return
    
    # Start server
    print("🔄 Starting server at http://localhost:8000")
    print("📚 API documentation will be available at http://localhost:8000/docs")
    print("⏹️  Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([
            "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--reload-dir", "app",
            "--reload-dir", "../studysprint-db"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    start_development_server()