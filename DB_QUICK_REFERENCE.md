# StudySprint DB - Quick Reference Card

## 🚀 Essential Imports

```python
# Database Core
from studysprint_db.config.database import Base, create_database_engine, create_session_factory
from studysprint_db.config.settings import db_settings

# User System (Already Built)
from studysprint_db.models.user import User, UserSession, UserPreferences
from studysprint_db.schemas.user import UserCreate, UserResponse, UserPreferencesUpdate

# Utility Mixins for New Models
from studysprint_db.utils.mixins import ProgressMixin, MetadataMixin, ColorMixin, StatisticsMixin
```

## 📊 Key Models Available

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `User` | User accounts | email, username, hashed_password, stats |
| `UserSession` | JWT sessions | user_id, session_token, expires_at |
| `UserPreferences` | User settings | theme, study_duration, notifications |

## 🧰 Model Creation Pattern

```python
# New model template
class YourModel(Base, MetadataMixin):  # Add mixins as needed
    __tablename__ = "your_table"
    
    # Foreign key to user (common pattern)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Your fields
    name = Column(String(255), nullable=False)
    
    # Relationships
    user = relationship("User")
```

## 📋 Schema Creation Pattern

```python
class YourModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    
class YourModelResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

## 🔄 Service Pattern

```python
from sqlalchemy.orm import Session

class YourService:
    @staticmethod
    def create_item(db: Session, user_id: str, item_data):
        db_item = YourModel(user_id=user_id, **item_data.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
```

## 📝 Migration Workflow

```bash
# 1. Add new model to studysprint_db/models/
# 2. Import in studysprint_db/models/__init__.py
# 3. Create migration
alembic revision --autogenerate -m "Add your_table"
# 4. Apply migration
alembic upgrade head
```

## 🎯 Available Mixins

- `ProgressMixin` → progress_percentage, is_completed, completed_at
- `MetadataMixin` → metadata (JSONB), set/get/update methods
- `ColorMixin` → color field with validation
- `StatisticsMixin` → view_count, last_viewed_at

## 🗄️ Database Connection (Backend)

```python
# In backend services
from app.config.database import get_db
from sqlalchemy.orm import Session

def your_endpoint(db: Session = Depends(get_db)):
    # Use db session here
    pass
```

## 🔐 Current API Endpoints

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User authentication  
- `GET /api/v1/auth/me` - Get current user
- `GET /health/db` - Database health check

## 📦 Ready for Stage 3

The database package is ready to support:
- Topics (organize PDFs)
- PDFs (file management)  
- Exercises (attach to PDFs)
- Sessions (time tracking)
- Notes (Obsidian-style)
