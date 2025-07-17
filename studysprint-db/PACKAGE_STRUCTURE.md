# StudySprint DB Package Structure

## 📦 Package Organization

```
studysprint-db/
├── studysprint_db/              # Main package
│   ├── __init__.py             # Package initialization
│   ├── _version.py             # Version information
│   ├── cli.py                  # Command-line interface
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py        # Models package init
│   │   └── user.py            # User authentication models
│   ├── schemas/                # Pydantic validation schemas
│   │   ├── __init__.py        # Schemas package init
│   │   └── user.py            # User validation schemas
│   ├── config/                 # Configuration modules
│   │   ├── __init__.py        # Config package init
│   │   ├── database.py        # Database configuration
│   │   └── settings.py        # Settings management
│   ├── utils/                  # Utility modules
│   │   ├── __init__.py        # Utils package init
│   │   └── mixins.py          # Model mixins
│   ├── alembic/                # Database migrations
│   │   ├── env.py             # Alembic environment
│   │   ├── script.py.mako     # Migration template
│   │   └── versions/          # Migration files
│   └── tests/                  # Test suite
│       ├── __init__.py        # Tests package init
│       └── test_config.py     # Configuration tests
├── setup.py                    # Package setup configuration
├── pyproject.toml             # Modern Python packaging
├── requirements.txt           # Package dependencies
├── README.md                  # Package documentation
├── .gitignore                 # Git ignore rules
├── .env.example              # Environment variables template
└── alembic.ini               # Alembic configuration

```

## 🎯 Package Features

- **Clean Architecture**: Separation of models, schemas, and configuration
- **Type Safety**: Comprehensive Pydantic schemas for all operations
- **Migration Management**: Alembic for database version control
- **Utility Mixins**: Reusable model components
- **CLI Tools**: Command-line interface for database operations
- **Testing Framework**: Comprehensive test suite setup

## 🔧 Development Commands

```bash
# Install package in development mode
pip install -e .

# Run migrations
alembic upgrade head

# Run tests
pytest

# Check package version
studysprint-db --version
```

## 📊 Database Models

### User Authentication
- **User**: Main user accounts with profile information
- **UserSession**: JWT session management and tracking
- **UserPreferences**: User settings and customization

### Model Features
- UUID primary keys for all tables
- Automatic timestamp tracking (created_at, updated_at)
- Soft delete functionality
- Relationship management with SQLAlchemy
- JSON metadata storage with JSONB columns

## 🔐 Security Features

- Bcrypt password hashing
- JWT token management
- Session tracking and expiration
- SQL injection protection via SQLAlchemy ORM
- Input validation via Pydantic schemas

This package provides a robust, scalable foundation for the StudySprint 2.0 application.
