"""
StudySprint 2.0 Database Package

This package contains all database models, schemas, and migrations for StudySprint 2.0.
It provides a clean separation between database concerns and business logic.

Usage:
    from studysprint_db.models.user import User
    from studysprint_db.schemas.user import UserCreate
    from studysprint_db.config.database import Base, create_database_engine
"""

from studysprint_db._version import __version__, __version_info__

# Package metadata
__title__ = "studysprint-db"
__description__ = "StudySprint 2.0 Database Models and Migrations"
__author__ = "StudySprint Team"
__email__ = "dev@studysprint.com"
__license__ = "MIT"

# Version exports
__all__ = [
    "__version__",
    "__version_info__",
    "__title__",
    "__description__",
    "__author__",
    "__email__",
    "__license__",
]

# Ensure compatibility
import sys
if sys.version_info < (3, 11):
    raise RuntimeError(
        f"StudySprint DB requires Python 3.11 or higher. "
        f"Current version: {sys.version_info.major}.{sys.version_info.minor}"
    )
