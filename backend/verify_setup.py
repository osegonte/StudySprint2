# backend/verify_setup.py
"""Verification script to check if Stage 3.2 is set up correctly"""

import os
import sys
import importlib.util

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - Missing: {filepath}")
        return False

def check_import(module_name, description):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        print(f"❌ {description} - Import error: {e}")
        return False

def check_directory_structure():
    """Check if the directory structure is correct"""
    print("📁 Checking directory structure...")
    
    required_files = [
        ("app/__init__.py", "App package init"),
        ("app/main.py", "Main FastAPI application"),
        ("app/models.py", "Consolidated models file"),
        ("app/schemas.py", "Consolidated schemas file"),
        ("app/config/__init__.py", "Config package init"),
        ("app/config/database.py", "Database configuration"),
        ("app/config/settings.py", "Application settings"),
        ("app/api/__init__.py", "API package init"),
        ("app/api/v1/__init__.py", "API v1 package init"),
        ("app/api/v1/auth.py", "Authentication endpoints"),
        ("app/api/v1/topics.py", "Topics endpoints"),
        ("app/services/__init__.py", "Services package init"),
        ("app/services/auth_service.py", "Authentication service"),
        ("app/services/topic_service.py", "Topic service"),
        ("app/utils/__init__.py", "Utils package init"),
        ("app/utils/crud_router.py", "CRUD router factory"),
        ("requirements-dev.txt", "Development dependencies"),
        ("alembic.ini", "Alembic configuration"),
    ]
    
    success_count = 0
    for filepath, description in required_files:
        if check_file_exists(filepath, description):
            success_count += 1
    
    return success_count, len(required_files)

def check_imports():
    """Check if all critical modules can be imported"""
    print("\n📦 Checking imports...")
    
    imports_to_check = [
        ("fastapi", "FastAPI framework"),
        ("sqlalchemy", "SQLAlchemy ORM"),
        ("pydantic", "Pydantic validation"),
        ("uvicorn", "ASGI server"),
        ("alembic", "Database migrations"),
        ("studysprint_db", "StudySprint DB package"),
    ]
    
    success_count = 0
    for module_name, description in imports_to_check:
        if check_import(module_name, description):
            success_count += 1
    
    return success_count, len(imports_to_check)

def check_app_imports():
    """Check if app modules can be imported"""
    print("\n🏗️ Checking app module imports...")
    
    app_imports = [
        ("app.main", "Main application"),
        ("app.config.settings", "Settings configuration"),
        ("app.config.database", "Database configuration"),
        ("app.models", "Consolidated models"),
        ("app.schemas", "Consolidated schemas"),
        ("app.services.auth_service", "Authentication service"),
        ("app.services.topic_service", "Topic service"),
        ("app.utils.crud_router", "CRUD router factory"),
        ("app.api.v1.auth", "Auth endpoints"),
        ("app.api.v1.topics", "Topic endpoints"),
    ]
    
    success_count = 0
    for module_name, description in app_imports:
        if check_import(module_name, description):
            success_count += 1
    
    return success_count, len(app_imports)

def check_environment():
    """Check environment setup"""
    print("\n🌍 Checking environment...")
    
    checks = []
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ Virtual environment detected")
        checks.append(True)
    else:
        print("⚠️  Virtual environment not detected (recommended but not required)")
        checks.append(False)
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 11):
        print(f"✅ Python version {python_version.major}.{python_version.minor} (compatible)")
        checks.append(True)
    else:
        print(f"❌ Python version {python_version.major}.{python_version.minor} (requires 3.11+)")
        checks.append(False)
    
    # Check if .env file exists
    if os.path.exists(".env"):
        print("✅ Environment file (.env) exists")
        checks.append(True)
    else:
        print("⚠️  Environment file (.env) not found (will use defaults)")
        checks.append(False)
    
    return sum(checks), len(checks)

def check_database_files():
    """Check database-related files"""
    print("\n🗄️ Checking database setup...")
    
    db_checks = []
    
    # Check if studysprint-db directory exists
    studysprint_db_path = "../studysprint-db"
    if os.path.exists(studysprint_db_path):
        print("✅ StudySprint DB package directory exists")
        db_checks.append(True)
    else:
        print("❌ StudySprint DB package directory missing")
        db_checks.append(False)
    
    # Check alembic directory
    if os.path.exists("alembic"):
        print("✅ Alembic directory exists")
        db_checks.append(True)
    else:
        print("❌ Alembic directory missing")
        db_checks.append(False)
    
    # Check if alembic env.py exists
    if os.path.exists("alembic/env.py"):
        print("✅ Alembic env.py exists")
        db_checks.append(True)
    else:
        print("❌ Alembic env.py missing")
        db_checks.append(False)
    
    return sum(db_checks), len(db_checks)

def main():
    """Main verification function"""
    print("🔍 StudySprint 2.0 - Stage 3.2 Setup Verification")
    print("=" * 55)
    
    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Not in backend directory. Please run from StudySprint2/backend/")
        sys.exit(1)
    
    # Run all checks
    dir_success, dir_total = check_directory_structure()
    import_success, import_total = check_imports()
    app_success, app_total = check_app_imports()
    env_success, env_total = check_environment()
    db_success, db_total = check_database_files()
    
    # Calculate overall score
    total_success = dir_success + import_success + app_success + env_success + db_success
    total_checks = dir_total + import_total + app_total + env_total + db_total
    
    percentage = (total_success / total_checks) * 100
    
    print("\n" + "=" * 55)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 55)
    print(f"Directory Structure: {dir_success}/{dir_total}")
    print(f"Dependencies: {import_success}/{import_total}")
    print(f"App Modules: {app_success}/{app_total}")
    print(f"Environment: {env_success}/{env_total}")
    print(f"Database Setup: {db_success}/{db_total}")
    print("-" * 55)
    print(f"Overall Score: {total_success}/{total_checks} ({percentage:.1f}%)")
    
    if percentage >= 90:
        print("\n🎉 EXCELLENT! Setup is complete and ready.")
        print("Next steps:")
        print("1. Start database: docker-compose up -d postgres redis")
        print("2. Run migrations: alembic upgrade head")
        print("3. Start server: uvicorn app.main:app --reload")
        print("4. Test: python test_stage3_topics.py")
    elif percentage >= 75:
        print("\n✅ GOOD! Setup is mostly complete with minor issues.")
        print("Review the ❌ items above and fix them.")
    elif percentage >= 50:
        print("\n⚠️  PARTIAL! Setup has some issues that need attention.")
        print("Please fix the ❌ items above before proceeding.")
    else:
        print("\n❌ INCOMPLETE! Major setup issues detected.")
        print("Please review the troubleshooting guide and fix critical issues.")
    
    return percentage >= 75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)