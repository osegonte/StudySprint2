#!/bin/bash

# StudySprint 2.0 - Quick Start Script

echo "🚀 Starting StudySprint 2.0..."

# Start all services with Docker
docker-compose up -d

echo "✅ Services started!"
echo ""
echo "🌐 Access points:"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"
echo ""
echo "📋 Useful commands:"
echo "- View logs: docker-compose logs -f"
echo "- Stop services: docker-compose down"
echo "- Restart services: docker-compose restart"
