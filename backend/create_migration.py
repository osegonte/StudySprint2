# backend/create_migration.py
"""Script to create Alembic migration for new models"""

import os
import subprocess
import sys

def create_migration():
    """Create migration for Stage 3 models"""
    
    print("🔄 Creating Alembic migration for Stage 3 models...")
    
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    try:
        # Create migration
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", 
            "-m", "Add Stage 3 models: Topics, PDFs, Sessions, Notes, Analytics"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration created successfully!")
            print(f"Migration file: {result.stdout}")
        else:
            print("❌ Migration creation failed!")
            print(f"Error: {result.stderr}")
            return False
        
        # Apply migration
        print("\n🔄 Applying migration...")
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration applied successfully!")
        else:
            print("❌ Migration application failed!")
            print(f"Error: {result.stderr}")
            return False
        
        return True
        
    except FileNotFoundError:
        print("❌ Alembic not found. Make sure you're in the backend directory with venv activated.")
        return False

if __name__ == "__main__":
    success = create_migration()
    sys.exit(0 if success else 1)
