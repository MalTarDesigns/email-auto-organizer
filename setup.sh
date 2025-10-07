#!/bin/bash

# Email Triage System - Setup Script

set -e

echo "========================================="
echo "Email Triage System - Initial Setup"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys and credentials"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Build containers
echo "🔨 Building Docker containers..."
docker-compose build
echo ""

# Start services
echo "🚀 Starting services..."
docker-compose up -d
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Run migrations
echo "📊 Running database migrations..."
docker-compose exec -T backend alembic upgrade head
echo ""

# Show status
echo "📋 Service Status:"
docker-compose ps
echo ""

echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Services are running at:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f          # View logs"
echo "  docker-compose down             # Stop services"
echo "  docker-compose exec backend bash   # Backend shell"
echo ""
echo "⚠️  Don't forget to configure your .env file with:"
echo "  - OPENAI_API_KEY"
echo "  - GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
echo "  - SECRET_KEY (generate a secure random string)"
echo ""
