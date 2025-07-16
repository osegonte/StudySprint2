#!/bin/bash

# StudySprint 2.0 - Database Setup Script

echo "🗄️ Setting up StudySprint 2.0 database..."

# Start PostgreSQL with Docker
echo "🐳 Starting PostgreSQL container..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Initialize Alembic
echo "🔧 Initializing Alembic migrations..."
cd backend
source venv/bin/activate
alembic init alembic

echo "✅ Database setup complete!"
echo ""
echo "Next steps:"
echo "1. Create your first migration: alembic revision --autogenerate -m 'Initial migration'"
echo "2. Apply migration: alembic upgrade head"
