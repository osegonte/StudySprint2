# backend/alembic/env.py  
"""Updated Alembic environment to include all Stage 3 models"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add the package to Python path
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)
sys.path.insert(0, parent_path)

# Import database configuration with all models
from app.config.database import Base
from app.config.settings import settings

# Import ALL models to ensure they're registered
from studysprint_db.models.user import User, UserSession, UserPreferences
from app.models import (
    Topic, PDF, ExerciseSet, Exercise, ExercisePageLink,
    StudySession, PageTime, PomodoroSession, 
    Note, NoteLink, NoteTag, Highlight, NoteAttachment,
    ReadingSpeed, TimeEstimate, UserStatistic,
    Goal, GoalProgress
)

# Alembic Config object
config = context.config

# Override the database URL with our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
