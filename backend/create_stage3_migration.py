# backend/create_stage3_migration.py
"""Script to create and apply Stage 3.3 migration"""

import os
import subprocess
import sys
from pathlib import Path

def create_and_apply_migration():
    """Create and apply migration for Stage 3.3 PDF models"""
    
    print("🗄️ Creating Stage 3.3 Migration: PDF Management Models")
    print("=" * 60)
    
    # Ensure we're in the backend directory
    if not Path("app").exists():
        print("❌ Please run from the backend/ directory")
        sys.exit(1)
    
    try:
        # Step 1: Create migration
        print("1. Creating Alembic migration...")
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", 
            "-m", "Add Stage 3.3 PDF management models"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration created successfully!")
            print(f"Output: {result.stdout}")
        else:
            print("❌ Migration creation failed!")
            print(f"Error: {result.stderr}")
            return False
        
        # Step 2: Apply migration
        print("\n2. Applying migration...")
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration applied successfully!")
            print(f"Output: {result.stdout}")
        else:
            print("❌ Migration application failed!")
            print(f"Error: {result.stderr}")
            return False
        
        # Step 3: Verify tables were created
        print("\n3. Verifying database tables...")
        try:
            from app.config.database import engine
            from sqlalchemy import inspect
            
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            expected_tables = [
                'topics', 'pdfs', 'exercise_sets', 'exercises', 'exercise_page_links'
            ]
            
            created_tables = []
            for table in expected_tables:
                if table in tables:
                    created_tables.append(table)
                    print(f"✅ Table '{table}' created")
                else:
                    print(f"❌ Table '{table}' not found")
            
            if len(created_tables) == len(expected_tables):
                print(f"\n🎉 All {len(created_tables)} tables created successfully!")
                return True
            else:
                print(f"\n⚠️  Only {len(created_tables)}/{len(expected_tables)} tables created")
                return False
                
        except Exception as e:
            print(f"❌ Table verification failed: {e}")
            return False
        
    except FileNotFoundError:
        print("❌ Alembic not found. Make sure you're in the backend directory with venv activated.")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def check_prerequisites():
    """Check if prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if alembic is installed
    try:
        result = subprocess.run(["alembic", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Alembic is installed")
        else:
            print("❌ Alembic not working properly")
            return False
    except FileNotFoundError:
        print("❌ Alembic not found. Run: pip install alembic")
        return False
    
    # Check if database is accessible
    try:
        from app.config.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection working")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure PostgreSQL is running and accessible")
        return False
    
    # Check if models can be imported
    try:
        from app.models import Topic, PDF, ExerciseSet, Exercise, ExercisePageLink
        print("✅ All models imported successfully")
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🚀 StudySprint 2.0 - Stage 3.3 Migration Setup")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        sys.exit(1)
    
    print("\n✅ Prerequisites met. Proceeding with migration...")
    
    # Create and apply migration
    if create_and_apply_migration():
        print("\n" + "=" * 60)
        print("🎉 STAGE 3.3 MIGRATION COMPLETED!")
        print("✅ Database models created:")
        print("   • topics - Topic organization")
        print("   • pdfs - PDF file management")
        print("   • exercise_sets - Exercise collections")
        print("   • exercises - Individual exercises")
        print("   • exercise_page_links - Exercise-to-page mapping")
        print("\n🚀 Ready to test PDF management features!")
        
        # Show next steps
        print("\n📋 Next steps:")
        print("1. Start the server: uvicorn app.main:app --reload")
        print("2. Test PDF upload: POST /api/v1/pdfs/upload")
        print("3. Run comprehensive tests: python test_stage3_pdfs.py")
        
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()