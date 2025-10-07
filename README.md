# Email Triage System

AI-powered email management and response generation system built with FastAPI, Next.js, and OpenAI.

## Features

- **Intelligent Email Triage**: Automatically categorize and prioritize incoming emails
- **AI-Powered Responses**: Generate contextual email responses using GPT-4
- **Gmail Integration**: Seamless OAuth integration with Gmail
- **Real-time Processing**: Background task processing with Celery
- **Modern UI**: Built with Next.js 14 and Tailwind CSS

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Primary database with pgvector for embeddings
- **Redis**: Caching and message broker for Celery
- **Celery**: Asynchronous task processing
- **OpenAI**: GPT-4 for email classification and response generation
- **Alembic**: Database migrations

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **React Query**: Data fetching and state management
- **Zustand**: Client-side state management

## Project Structure

```
email-auto-organizer/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Configuration
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── workers/          # Celery tasks
│   ├── alembic/              # Database migrations
│   ├── tests/                # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js app directory
│   ├── components/           # React components
│   ├── lib/                  # Utilities
│   ├── types/                # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for local development)
- OpenAI API key
- Google OAuth credentials (for Gmail integration)

### Environment Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Update `.env` with your credentials:
```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Security
SECRET_KEY=your_secret_key_here_min_32_characters
```

### Running with Docker

1. Build and start all services:
```bash
docker-compose up --build
```

2. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

3. Access the services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the server:
```bash
uvicorn app.main:app --reload
```

#### Frontend

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

## Database Migrations

Create a new migration:
```bash
docker-compose exec backend alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
docker-compose exec backend alembic upgrade head
```

Rollback migration:
```bash
docker-compose exec backend alembic downgrade -1
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Phases

- [x] **Phase 1**: Project Setup & Infrastructure
- [ ] **Phase 2**: Email Integration (Gmail OAuth)
- [ ] **Phase 3**: AI-Powered Triage System
- [ ] **Phase 4**: Response Generation
- [ ] **Phase 5**: Frontend Development
- [ ] **Phase 6**: API Endpoints
- [ ] **Phase 7**: Testing & Quality Assurance
- [ ] **Phase 8**: Deployment & Production

## Testing

Run backend tests:
```bash
docker-compose exec backend pytest
```

Run frontend tests:
```bash
cd frontend && npm test
```

## License

This project is licensed under the MIT License.
