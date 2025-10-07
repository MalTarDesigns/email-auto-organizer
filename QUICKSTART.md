# Email Triage System - Quick Start Guide

## Prerequisites

Before you begin, ensure you have:
- **Docker Desktop** installed and running
- **Git** installed
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **Google OAuth Credentials** ([Setup guide](https://developers.google.com/identity/protocols/oauth2))

## Setup (5 Minutes)

### 1. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and fill in these required values:
```env
# OpenAI (Required)
OPENAI_API_KEY=sk-...your-key-here

# Google OAuth (Required for Gmail)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Security (Generate a random 32+ character string)
SECRET_KEY=your-super-secret-key-min-32-chars
```

### 2. Start the Application

#### Option A: Automated Setup (Recommended)
```bash
chmod +x setup.sh
./setup.sh
```

#### Option B: Manual Setup
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Check status
docker-compose ps
```

### 3. Verify Installation

Open your browser and visit:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

You should see:
- Frontend: "Email Triage System" homepage
- Backend: JSON response with `{"message": "Email Triage System API", ...}`
- API Docs: Interactive Swagger UI

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Access Service Shells
```bash
# Backend Python shell
docker-compose exec backend bash

# Frontend Node shell
docker-compose exec frontend sh
```

### Database Operations
```bash
# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

### Run Tests
```bash
# Backend tests
docker-compose exec backend pytest

# With coverage report
docker-compose exec backend pytest --cov=app --cov-report=html
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Troubleshooting

### Port Already in Use
If you see "port already allocated" error:
```bash
# Check what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Stop the process or change port in docker-compose.yml
```

### Database Connection Issues
```bash
# Ensure PostgreSQL is running
docker-compose ps

# Check PostgreSQL logs
docker-compose logs postgres

# Recreate database
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Backend Not Starting
```bash
# View error logs
docker-compose logs backend

# Rebuild backend
docker-compose build backend
docker-compose up -d backend
```

### Frontend Build Errors
```bash
# Clear node_modules and reinstall
docker-compose down
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

## Development Workflow

### Making Code Changes

Backend and frontend have hot-reload enabled:
- **Backend**: Changes to `.py` files auto-reload FastAPI
- **Frontend**: Changes to `.tsx/.ts` files auto-reload Next.js

### Adding Dependencies

#### Backend (Python)
1. Add package to `backend/requirements.txt`
2. Rebuild: `docker-compose build backend`
3. Restart: `docker-compose up -d backend`

#### Frontend (Node)
1. Add package to `frontend/package.json` or use:
   ```bash
   docker-compose exec frontend npm install <package>
   ```
2. Restart: `docker-compose restart frontend`

## Next Steps

1. **Phase 2**: Implement Gmail OAuth integration
2. **Phase 3**: Build AI-powered email triage system
3. **Phase 4**: Add response generation
4. **Phase 5**: Build frontend UI

## Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## Getting Help

- Check `SETUP_COMPLETE.md` for detailed setup info
- Review `PROJECT_STRUCTURE.md` for codebase layout
- See `README.md` for comprehensive documentation
- Check phase specs in `specs/phases/` directory

## Health Check

Verify everything is working:
```bash
# Check all services are running
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# Run backend tests
docker-compose exec backend pytest -v
```

Expected output: All services "Up", health check returns `{"status": "healthy"}`, tests pass ✅
