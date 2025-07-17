"""Database-specific settings - FORCED PORT 5433"""

class DatabaseSettings:
    """Database configuration settings"""
    DATABASE_URL = "postgresql://studysprint:password@localhost:5433/studysprint2"
    DB_ECHO = False
    DB_POOL_SIZE = 5

# Force the correct URL
db_settings = DatabaseSettings()
