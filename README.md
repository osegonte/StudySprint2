# StudySprint 2.0 🚀

Advanced PDF Study Management System with AI-powered features, smart time tracking, and Obsidian-style note-taking.

## 🏗️ Project Structure

```
StudySprint2/
├── backend/                     # Python FastAPI Backend
│   ├── app/                    # Main application code
│   │   ├── config/            # Configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/               # API routes
│   │   ├── services/          # Business logic
│   │   └── utils/             # Utilities
│   ├── alembic/               # Database migrations
│   ├── storage/               # File storage
│   └── tests/                 # Test suite
├── frontend/                   # React Frontend (Future)
├── database/                   # Database scripts
├── docker/                     # Docker configurations
└── scripts/                    # Utility scripts
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Clone and setup:**
   ```bash
   # Project structure is already created
   cd StudySprint2
   ```

2. **Start services:**
   ```bash
   ./scripts/start.sh
   ```

3. **Access the application:**
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Local Development

1. **Setup development environment:**
   ```bash
   ./scripts/setup-dev.sh
   ```

2. **Setup database:**
   ```bash
   ./scripts/setup-db.sh
   ```

3. **Start backend:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

## 🔧 Development

### Environment Variables

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

### Database Migrations

```bash
cd backend
source venv/bin/activate

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Testing

```bash
cd backend
source venv/bin/activate
pytest
```

## 📦 Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Authentication**: JWT tokens
- **File Storage**: Local filesystem (S3 ready)
- **Task Queue**: Redis (Celery ready)
- **Frontend**: React + TypeScript (Stage 8+)

## 🎯 Development Stages

- ✅ **Stage 1**: Project Foundation (Current)
- 🔲 **Stage 2**: Database Foundation
- 🔲 **Stage 3**: Backend Core Services
- 🔲 **Stage 4**: Timer & Analytics Services
- 🔲 **Stage 5**: Notes & Knowledge Services
- 🔲 **Stage 6**: Goals & Analytics Services
- 🔲 **Stage 7**: Backend Testing & Optimization
- 🔲 **Stage 8+**: Frontend Development

## 📚 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## 🤝 Contributing

1. Follow the staged development plan
2. Write tests for new features
3. Update documentation
4. Use conventional commits

## 📄 License

MIT License - see LICENSE file for details.
