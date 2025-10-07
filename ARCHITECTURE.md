# Email Triage System - Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Next.js 14 Frontend (Port 3000)                             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │  │
│  │  │ React      │  │ TypeScript │  │ Tailwind   │             │  │
│  │  │ Components │  │ Types      │  │ CSS        │             │  │
│  │  └────────────┘  └────────────┘  └────────────┘             │  │
│  │                                                               │  │
│  │  ┌────────────┐  ┌────────────┐                             │  │
│  │  │ React      │  │ Zustand    │                             │  │
│  │  │ Query      │  │ State      │                             │  │
│  │  └────────────┘  └────────────┘                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                             │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (Port 8000)                                 │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────────────────────────────┐ │  │
│  │  │                   API Routes                            │ │  │
│  │  │  /api/v1/auth    /api/v1/emails    /api/v1/responses  │ │  │
│  │  └────────────────────────────────────────────────────────┘ │  │
│  │                            │                                  │  │
│  │  ┌─────────────┐  ┌───────┴────────┐  ┌─────────────────┐  │  │
│  │  │   OAuth     │  │    Business    │  │   AI Service    │  │  │
│  │  │   Service   │  │     Logic      │  │   (OpenAI)      │  │  │
│  │  └─────────────┘  └────────────────┘  └─────────────────┘  │  │
│  │                            │                                  │  │
│  │  ┌─────────────────────────┴─────────────────────────────┐  │  │
│  │  │              Pydantic Schemas & Validation            │  │  │
│  │  └───────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Celery Workers                                              │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │  │
│  │  │   Email     │  │    Email     │  │    Response      │   │  │
│  │  │   Sync      │  │  Processing  │  │   Generation     │   │  │
│  │  └─────────────┘  └──────────────┘  └──────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                          │                    │
                          ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│                                                                       │
│  ┌─────────────────────────────┐  ┌────────────────────────────┐   │
│  │  PostgreSQL 15 (Port 5432)  │  │  Redis 7 (Port 6379)       │   │
│  │                             │  │                             │   │
│  │  ┌──────────────────────┐  │  │  ┌──────────────────────┐  │   │
│  │  │  Tables:             │  │  │  │  Features:           │  │   │
│  │  │  - users             │  │  │  │  - Session cache     │  │   │
│  │  │  - emails            │  │  │  │  - Celery broker     │  │   │
│  │  │  - classifications   │  │  │  │  - Result backend    │  │   │
│  │  │  - responses         │  │  │  │  - Token storage     │  │   │
│  │  │  - preferences       │  │  │  └──────────────────────┘  │   │
│  │  │  - feedback          │  │  │                             │   │
│  │  └──────────────────────┘  │  └────────────────────────────┘   │
│  │                             │                                    │
│  │  ┌──────────────────────┐  │                                    │
│  │  │  Extensions:         │  │                                    │
│  │  │  - uuid-ossp         │  │                                    │
│  │  │  - pgvector(1536)    │  │                                    │
│  │  └──────────────────────┘  │                                    │
│  └─────────────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                               │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Gmail API  │  │  OpenAI API  │  │  Google OAuth 2.0        │  │
│  │              │  │              │  │                          │  │
│  │  - Fetch     │  │  - GPT-4     │  │  - Authentication        │  │
│  │  - Send      │  │  - Embeddings│  │  - Token Management      │  │
│  │  - Labels    │  │  - Classify  │  │  - Refresh Tokens        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow Diagrams

### 1. Email Processing Flow

```
User Connects Gmail Account
         │
         ▼
┌─────────────────────┐
│  OAuth Flow         │
│  - Authorize        │
│  - Exchange Code    │
│  - Store Tokens     │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Trigger Email Sync │
│  (Celery Task)      │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Fetch Emails       │
│  from Gmail API     │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Parse & Store      │
│  in PostgreSQL      │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Queue Processing   │
│  Task per Email     │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  AI Classification  │
│  - Category         │
│  - Priority         │
│  - Sentiment        │
│  - Urgency Score    │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Generate Embedding │
│  (OpenAI)           │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Store Results      │
│  & Update UI        │
└─────────────────────┘
```

### 2. Response Generation Flow

```
User Selects Email
         │
         ▼
┌─────────────────────┐
│  Request Response   │
│  - Tone: Professional│
│  - Length: Medium    │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Retrieve Context   │
│  - Email Thread     │
│  - User Preferences │
│  - Similar Emails   │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  OpenAI API Call    │
│  - GPT-4 Prompt     │
│  - Context Injection│
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Store Response     │
│  - Draft Text       │
│  - Metadata         │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Display to User    │
│  - Edit Option      │
│  - Approve/Reject   │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  User Action        │
│  ├─ Approve: Send   │
│  ├─ Edit: Update    │
│  └─ Reject: Log     │
└─────────────────────┘
```

## Data Flow Architecture

### Database Schema Relationships

```
┌─────────────┐
│    users    │
│─────────────│
│ id (PK)     │────┐
│ email       │    │
│ tokens      │    │
└─────────────┘    │
                   │
        ┌──────────┴────────────────────────────┐
        │                                        │
        ▼                                        ▼
┌─────────────────┐                    ┌─────────────────┐
│     emails      │                    │ user_preferences│
│─────────────────│                    │─────────────────│
│ id (PK)         │───┐                │ id (PK)         │
│ user_id (FK)    │   │                │ user_id (FK)    │
│ message_id      │   │                │ auto_triage     │
│ subject         │   │                │ response_tone   │
│ body_text       │   │                │ rules (JSONB)   │
│ category        │   │                └─────────────────┘
│ priority        │   │
│ embedding       │   │
└─────────────────┘   │
                      │
        ┌─────────────┴─────────────────────────┐
        │                                        │
        ▼                                        ▼
┌──────────────────────┐              ┌────────────────────┐
│ email_classifications│              │ generated_responses│
│──────────────────────│              │────────────────────│
│ id (PK)              │              │ id (PK)            │
│ email_id (FK)        │              │ email_id (FK)      │
│ type                 │              │ response_text      │
│ value                │              │ tone               │
│ confidence           │              │ user_approved      │
└──────────────────────┘              │ sent_at            │
                                      └────────────────────┘
                                               │
                                               ▼
                                      ┌────────────────────┐
                                      │   user_feedback    │
                                      │────────────────────│
                                      │ id (PK)            │
                                      │ response_id (FK)   │
                                      │ rating             │
                                      │ corrected_category │
                                      └────────────────────┘
```

## Technology Stack Details

### Backend Stack
```
FastAPI (0.109.0)
├── Uvicorn (ASGI Server)
├── Pydantic (Validation)
├── SQLAlchemy (ORM)
│   └── PostgreSQL Driver (asyncpg, psycopg2)
├── Alembic (Migrations)
├── Celery (Task Queue)
│   └── Redis (Broker)
├── OpenAI SDK
└── Google API Client
```

### Frontend Stack
```
Next.js 14
├── React 18
├── TypeScript
├── Tailwind CSS
├── React Query (Data Fetching)
├── Zustand (State Management)
└── Axios (HTTP Client)
```

### Infrastructure Stack
```
Docker Compose
├── PostgreSQL 15
│   ├── uuid-ossp Extension
│   └── pgvector Extension
├── Redis 7
│   ├── Cache Layer
│   └── Message Broker
└── Node/Python Containers
```

## Security Architecture

### Authentication Flow
```
1. User → Frontend → OAuth Redirect → Google
2. Google → Callback → Backend
3. Backend → Validate → Exchange Code for Tokens
4. Backend → Generate JWT → Store in httpOnly Cookie
5. Backend → Encrypt & Store OAuth Tokens in DB
6. Frontend → Include JWT in Requests
7. Backend → Verify JWT → Grant Access
```

### Data Protection
- ✅ Passwords: bcrypt hashing (12 rounds)
- ✅ Tokens: Encrypted at rest in PostgreSQL
- ✅ API Keys: Environment variables only
- ✅ JWT: HS256 with secret key rotation
- ✅ HTTPS: Required in production
- ✅ CORS: Whitelist origins only

## Scalability Design

### Horizontal Scaling Points
1. **FastAPI Backend**: Stateless, can run multiple instances
2. **Celery Workers**: Add workers as load increases
3. **PostgreSQL**: Read replicas for queries
4. **Redis**: Cluster mode for high availability
5. **Frontend**: CDN for static assets

### Performance Optimizations
- Database connection pooling (10-20 connections)
- Redis caching for frequent queries
- Background task processing (Celery)
- Vector similarity search (pgvector)
- Lazy loading on frontend
- API response pagination (50-100 items)

## Monitoring Points

### Health Checks
- **Backend**: `/health` endpoint
- **Database**: PostgreSQL pg_isready
- **Redis**: PING command
- **Celery**: Worker heartbeat

### Metrics to Track
- Email processing time
- AI classification accuracy
- Response generation latency
- Database query performance
- Cache hit rates
- Worker queue depth

## Development Workflow

```
Developer
    │
    ├─── Backend Changes
    │    ├─ Edit Python files
    │    ├─ Auto-reload (uvicorn --reload)
    │    └─ Run pytest
    │
    └─── Frontend Changes
         ├─ Edit TypeScript/React files
         ├─ Auto-reload (Next.js Fast Refresh)
         └─ View in browser
```

## Deployment Architecture (Future)

```
                    ┌─────────────┐
                    │   CDN       │
                    │ (Vercel)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Frontend  │
                    │  (Vercel)   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────────┐
                    │  Load Balancer  │
                    │   (AWS ALB)     │
                    └──────┬──────────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
    ┌──────▼──────┐              ┌────────▼────────┐
    │   Backend   │              │  Celery Workers │
    │ (AWS ECS)   │              │    (AWS ECS)    │
    └──────┬──────┘              └────────┬────────┘
           │                               │
           └───────────────┬───────────────┘
                           │
                    ┌──────▼──────────┐
                    │   PostgreSQL    │
                    │    (AWS RDS)    │
                    └─────────────────┘
                           │
                    ┌──────▼──────────┐
                    │   Redis         │
                    │ (AWS ElastiCache)│
                    └─────────────────┘
```

## Summary

This architecture provides:
- ✅ **Scalability**: Horizontal scaling of all components
- ✅ **Reliability**: Health checks and service dependencies
- ✅ **Performance**: Caching, async processing, connection pooling
- ✅ **Security**: OAuth, JWT, encryption, validation
- ✅ **Maintainability**: Clear separation of concerns, typed code
- ✅ **Observability**: Health endpoints, logging points, metrics ready
