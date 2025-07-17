"""
Command-line interface for StudySprint DB operations
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

def main() -> None:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="StudySprint DB Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  studysprint-db init          Initialize database
  studysprint-db migrate       Run database migrations
  studysprint-db version       Show package version
  studysprint-db test          Run database tests
        """
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"%(prog)s {get_version()}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument(
        "--url", 
        help="Database URL (default: from environment)"
    )
    init_parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force recreation of tables"
    )
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Run database migrations")
    migrate_parser.add_argument(
        "target", 
        nargs="?", 
        default="head", 
        help="Migration target (default: head)"
    )
    migrate_parser.add_argument(
        "--sql", 
        action="store_true", 
        help="Show SQL instead of executing"
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    version_parser.add_argument(
        "--db", 
        action="store_true", 
        help="Show database schema version"
    )
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run database tests")
    test_parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run with coverage report"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    try:
        if args.command == "init":
            init_command(args.url, args.force)
        elif args.command == "migrate":
            migrate_command(args.target, args.sql)
        elif args.command == "version":
            version_command(args.db)
        elif args.command == "test":
            test_command(args.coverage)
        else:
            parser.print_help()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def init_command(database_url: Optional[str] = None, force: bool = False) -> None:
    """Initialize database tables"""
    print("🏗️ Initializing StudySprint database...")
    
    try:
        from studysprint_db.config.database import Base, create_database_engine
        from studysprint_db.config.settings import db_settings
        
        # Import all models to register them
        try:
            import studysprint_db.models
            print("📦 Models imported successfully")
        except ImportError:
            print("⚠️ No models found yet - creating base structure")
        
        # Use provided URL or default
        url = database_url or db_settings.DATABASE_URL
        engine = create_database_engine(url)
        
        if force:
            print("⚠️ Dropping existing tables...")
            Base.metadata.drop_all(engine)
        
        print("📋 Creating database tables...")
        Base.metadata.create_all(engine)
        
        print("✅ Database initialized successfully!")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Run: pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


def migrate_command(target: str = "head", show_sql: bool = False) -> None:
    """Run database migrations using Alembic"""
    print(f"🔄 Running database migrations to {target}...")
    
    try:
        from alembic.config import Config
        from alembic import command
        
        # Find alembic.ini file
        alembic_cfg_path = find_alembic_config()
        if not alembic_cfg_path:
            print("❌ alembic.ini not found. Run: alembic init alembic")
            sys.exit(1)
        
        alembic_cfg = Config(alembic_cfg_path)
        
        if show_sql:
            command.upgrade(alembic_cfg, target, sql=True)
        else:
            command.upgrade(alembic_cfg, target)
            print("✅ Migrations completed successfully!")
            
    except ImportError:
        print("❌ Alembic not installed. Run: pip install alembic")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


def version_command(show_db_version: bool = False) -> None:
    """Show version information"""
    from studysprint_db._version import __version__, DB_SCHEMA_VERSION
    
    print(f"📦 StudySprint DB Package: v{__version__}")
    
    if show_db_version:
        print(f"🗄️ Database Schema: v{DB_SCHEMA_VERSION}")
        
        try:
            from alembic.config import Config
            from alembic import command
            from io import StringIO
            
            alembic_cfg_path = find_alembic_config()
            if alembic_cfg_path:
                alembic_cfg = Config(alembic_cfg_path)
                
                # Capture current revision
                output = StringIO()
                alembic_cfg.stdout = output
                command.current(alembic_cfg)
                current_rev = output.getvalue().strip()
                
                if current_rev:
                    print(f"🔄 Current Migration: {current_rev}")
                else:
                    print("🔄 Current Migration: No migrations applied")
            else:
                print("⚠️ Alembic not configured")
                
        except Exception as e:
            print(f"⚠️ Could not get database version: {e}")


def test_command(with_coverage: bool = False) -> None:
    """Run database tests"""
    print("🧪 Running StudySprint DB tests...")
    
    try:
        import pytest
        
        args = ["tests/"]
        
        if with_coverage:
            args.extend([
                "--cov=studysprint_db",
                "--cov-report=term-missing",
                "--cov-report=html"
            ])
        
        exit_code = pytest.main(args)
        
        if exit_code == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            sys.exit(exit_code)
            
    except ImportError:
        print("❌ pytest not installed. Run: pip install pytest")
        sys.exit(1)


def find_alembic_config() -> Optional[str]:
    """Find alembic.ini configuration file"""
    possible_paths = [
        "alembic.ini",
        "studysprint_db/alembic.ini",
        "../alembic.ini",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def get_version() -> str:
    """Get package version"""
    try:
        from studysprint_db._version import __version__
        return __version__
    except ImportError:
        return "unknown"


if __name__ == "__main__":
    main()
