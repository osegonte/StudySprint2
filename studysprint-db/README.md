# StudySprint DB Package 📊

Database models, schemas, and migrations for StudySprint 2.0 - Advanced PDF Study Management System.

## 🏗️ Architecture

This package provides a clean separation between database concerns and business logic:

- **Models**: SQLAlchemy ORM models with relationships
- **Schemas**: Pydantic models for data validation and serialization  
- **Migrations**: Alembic database migrations
- **Config**: Database configuration and connection management
- **Utils**: Database utilities and mixins

## 🚀 Quick Start

### Installation

```bash
# Install from local development
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Basic Usage

```python
from studysprint_db.config.database import Base, create_database_engine
from studysprint_db.models.user import User
from studysprint_db.schemas.user import UserCreate

# Create database engine
engine = create_database_engine("postgresql://user:pass@localhost/db")

# Create tables
Base.metadata.create_all(engine)

# Use models
user_data = UserCreate(email="user@example.com", username="user", password="pass")
```

### Running Migrations

```bash
# Initialize Alembic (first time only)
alembic init studysprint_db/alembic

# Create a new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Or use the CLI commands
studysprint-migrate upgrade head
studysprint-init-db
```

## 📁 Package Structure

```
studysprint_db/
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic schemas
├── config/           # Configuration
├── utils/            # Utilities
├── alembic/          # Migration files
└── tests/            # Test suite
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=studysprint_db --cov-report=html
```

## 📝 License

MIT License - see LICENSE file for details.
