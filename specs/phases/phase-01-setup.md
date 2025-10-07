# Phase 1: Project Setup & Infrastructure

**Timeline**: Week 1

## Objectives

- Initialize project directory structure
- Setup backend Python environment with FastAPI
- Configure Docker development environment
- Setup PostgreSQL database with schema
- Configure Redis for caching and queues
- Setup environment-based configuration

## 1.1 Initialize Project Structure

```bash
email-auto-organizer/
├── frontend/                 # Next.js application
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities and helpers
│   ├── types/               # TypeScript definitions
│   └── public/              # Static assets
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── workers/        # Celery tasks
│   └── tests/              # Backend tests
├── docker-compose.yml
├── .env.example
└── README.md
```

## 1.2 Setup Backend Environment

### Configuration File

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Email Triage System"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Email Provider (Gmail OAuth)
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
```

## 1.3 Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: email_triage
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/email_triage
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  celery_worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/email_triage
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

volumes:
  postgres_data:
```

## 1.4 Database Schema

### Core Tables

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    email_provider VARCHAR(50),
    access_token TEXT,
    refresh_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Emails Table
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    subject TEXT,
    sender_email VARCHAR(255),
    sender_name VARCHAR(255),
    body_text TEXT,
    body_html TEXT,
    received_at TIMESTAMP,
    processed_at TIMESTAMP,
    category VARCHAR(50),
    priority VARCHAR(20),
    urgency_score DECIMAL(3,2),
    sentiment VARCHAR(20),
    requires_action BOOLEAN DEFAULT FALSE,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_received (user_id, received_at DESC),
    INDEX idx_category (category),
    INDEX idx_priority (priority)
);

-- Email Classifications Table
CREATE TABLE email_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    classification_type VARCHAR(50),
    classification_value VARCHAR(100),
    confidence_score DECIMAL(3,2),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Generated Responses Table
CREATE TABLE generated_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    response_text TEXT NOT NULL,
    tone VARCHAR(50),
    length VARCHAR(20),
    model_used VARCHAR(50),
    generation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_approved BOOLEAN,
    user_edited BOOLEAN DEFAULT FALSE,
    final_response TEXT,
    sent_at TIMESTAMP,
    feedback_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email_responses (email_id, generation_timestamp DESC)
);

-- User Preferences Table
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    auto_triage_enabled BOOLEAN DEFAULT TRUE,
    auto_respond_enabled BOOLEAN DEFAULT FALSE,
    response_tone VARCHAR(50) DEFAULT 'professional',
    priority_rules JSONB,
    category_rules JSONB,
    blacklist_senders TEXT[],
    whitelist_senders TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Feedback & Learning Table
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email_id UUID REFERENCES emails(id) ON DELETE CASCADE,
    response_id UUID REFERENCES generated_responses(id) ON DELETE SET NULL,
    feedback_type VARCHAR(50),
    corrected_category VARCHAR(50),
    corrected_priority VARCHAR(20),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Deliverables

- ✅ Complete project directory structure
- ✅ Docker Compose configuration with all services
- ✅ PostgreSQL database with complete schema
- ✅ Redis cache and queue setup
- ✅ Backend configuration management
- ✅ Environment variables template (.env.example)
- ✅ Basic FastAPI application skeleton
- ✅ Database migrations setup (Alembic)

## Success Criteria

- Docker environment starts without errors
- Database connections successful
- Redis accessible from backend
- Environment configuration loads correctly
- All services communicate properly
