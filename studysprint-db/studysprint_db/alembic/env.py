"""Alembic environment configuration for StudySprint DB"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add the package to Python path
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.insert(0, parent_path)

# Import our database configuration
from studysprint_db.config.database import Base
from studysprint_db.config.settings import db_settings

# Import all models to ensure they're registered with SQLAlchemy
# (We'll add these imports as we create models)
try:
    # Import models here as they're created
    # from studysprint_db.models.user import User, UserSession, UserPreferences
    # from studysprint_db.models.topic import Topic
    # from studysprint_db.models.pdf import PDF, Exercise
    # from studysprint_db.models.session import StudySession
    # from studysprint_db.models.note import Note, Highlight
    pass
except ImportError:
    # Models not created yet
    pass

# Alembic Config object
config = context.config

# Override the database URL with our settings
config.set_main_option("sqlalchemy.url", db_settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
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
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
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
