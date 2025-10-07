# Smart Email Triage & Response Generator

## Problem Statement

Modern professionals receive overwhelming volumes of email daily, requiring significant time to read, categorize, prioritize, and respond appropriately. This system aims to automate email triage, classification, and intelligent response generation using AI, reducing manual effort while maintaining professional communication standards.

## Objectives

1. **Automated Email Classification**: Automatically categorize incoming emails by urgency, category, and required action
2. **Intelligent Prioritization**: Use AI to determine email importance and suggest priority levels
3. **Response Generation**: Generate contextually appropriate email responses using OpenAI's language models
4. **User Oversight**: Provide human-in-the-loop workflow for reviewing and approving AI-generated responses
5. **Learning System**: Continuously improve classification and response quality based on user feedback

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js/TypeScript)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Email Inbox  │  │ Triage Queue │  │ Response     │     │
│  │ Dashboard    │  │ & Filters    │  │ Editor       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (Python/FastAPI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Email        │  │ AI Triage    │  │ Response     │     │
│  │ Connector    │  │ Engine       │  │ Generator    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ OpenAI       │  │ Database     │  │ Queue        │     │
│  │ Integration  │  │ Layer        │  │ Worker       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   PostgreSQL  │
                    │   Database    │
                    └───────────────┘
```

### Technology Stack

**Frontend:**
- Next.js 14+ (App Router)
- TypeScript (strict mode)
- React 18+ with Server Components
- TailwindCSS for styling
- React Query for data fetching
- Zustand for state management

**Backend:**
- Python 3.11+
- FastAPI for REST API
- SQLAlchemy for ORM
- Pydantic for validation
- Celery for async task processing
- Redis for caching and queue management

**AI & ML:**
- OpenAI GPT-4 for response generation
- OpenAI Embeddings for semantic search
- Custom fine-tuning for classification

**Database:**
- PostgreSQL for primary data storage
- Redis for session and cache management

**Infrastructure:**
- Docker for containerization
- Docker Compose for local development
- Environment-based configuration

## Database Schema

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

## Implementation Plan

### Phase 1: Project Setup & Infrastructure (Week 1)

#### 1.1 Initialize Project Structure
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

#### 1.2 Setup Backend Environment
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

#### 1.3 Docker Configuration
```yaml
# docker-compose.yml
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

### Phase 2: Email Integration & Data Pipeline (Week 2)

#### 2.1 Gmail OAuth Integration
```python
# backend/app/services/email_service.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import base64

class EmailService:
    def __init__(self, user_credentials: dict):
        self.credentials = Credentials(**user_credentials)
        self.service = build('gmail', 'v1', credentials=self.credentials)

    async def fetch_emails(self, max_results: int = 50) -> list:
        """Fetch recent emails from Gmail"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()

            messages = results.get('messages', [])
            emails = []

            for msg in messages:
                email_data = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                emails.append(self._parse_email(email_data))

            return emails
        except Exception as e:
            raise Exception(f"Error fetching emails: {str(e)}")

    def _parse_email(self, email_data: dict) -> dict:
        """Parse Gmail API response into structured format"""
        headers = {h['name']: h['value']
                  for h in email_data['payload']['headers']}

        # Extract body
        body = ""
        if 'parts' in email_data['payload']:
            for part in email_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
                    break
        else:
            body = base64.urlsafe_b64decode(
                email_data['payload']['body']['data']
            ).decode('utf-8')

        return {
            'message_id': email_data['id'],
            'subject': headers.get('Subject', ''),
            'sender_email': headers.get('From', ''),
            'received_at': headers.get('Date', ''),
            'body_text': body,
            'snippet': email_data.get('snippet', '')
        }
```

#### 2.2 Email Processing Worker
```python
# backend/app/workers/email_processor.py
from celery import Celery
from app.services.triage_service import TriageService
from app.models.email import Email
from app.core.database import SessionLocal

celery_app = Celery('email_processor')

@celery_app.task
def process_email(email_id: str):
    """Background task to process and classify email"""
    db = SessionLocal()

    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            return {'error': 'Email not found'}

        triage_service = TriageService()

        # Classify email
        classification = triage_service.classify_email(
            subject=email.subject,
            body=email.body_text,
            sender=email.sender_email
        )

        # Update email with classification
        email.category = classification['category']
        email.priority = classification['priority']
        email.urgency_score = classification['urgency_score']
        email.sentiment = classification['sentiment']
        email.requires_action = classification['requires_action']

        db.commit()

        return {'status': 'processed', 'email_id': email_id}

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
```

### Phase 3: AI Triage Engine (Week 3)

#### 3.1 Email Classification Service
```python
# backend/app/services/triage_service.py
from openai import OpenAI
import json

class TriageService:
    def __init__(self):
        self.client = OpenAI()
        self.classification_prompt = """
        Analyze the following email and provide classification:

        Subject: {subject}
        From: {sender}
        Body: {body}

        Provide the following classifications:
        1. Category (work, personal, marketing, support, finance, other)
        2. Priority (urgent, high, medium, low)
        3. Urgency Score (0.0 to 1.0)
        4. Sentiment (positive, neutral, negative)
        5. Requires Action (true/false)
        6. Reasoning (brief explanation)

        Respond in JSON format.
        """

    def classify_email(self, subject: str, body: str, sender: str) -> dict:
        """Use OpenAI to classify email"""

        prompt = self.classification_prompt.format(
            subject=subject,
            sender=sender,
            body=body[:1000]  # Limit body length
        )

        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an email classification expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        classification = json.loads(response.choices[0].message.content)

        return {
            'category': classification.get('category', 'other'),
            'priority': classification.get('priority', 'medium'),
            'urgency_score': float(classification.get('urgency_score', 0.5)),
            'sentiment': classification.get('sentiment', 'neutral'),
            'requires_action': classification.get('requires_action', False),
            'reasoning': classification.get('reasoning', '')
        }

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for semantic search"""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
```

#### 3.2 Priority Rules Engine
```python
# backend/app/services/priority_engine.py
from typing import Dict, List
import re

class PriorityEngine:
    def __init__(self, user_preferences: dict):
        self.preferences = user_preferences
        self.priority_keywords = {
            'urgent': ['urgent', 'asap', 'immediate', 'critical', 'emergency'],
            'high': ['important', 'priority', 'deadline', 'today'],
            'medium': ['please review', 'feedback', 'update'],
            'low': ['fyi', 'newsletter', 'notification']
        }

    def apply_custom_rules(self, email: dict, ai_classification: dict) -> dict:
        """Apply user-defined rules to override or adjust AI classification"""

        # Check whitelist/blacklist
        if email['sender_email'] in self.preferences.get('whitelist_senders', []):
            ai_classification['priority'] = 'high'

        if email['sender_email'] in self.preferences.get('blacklist_senders', []):
            ai_classification['priority'] = 'low'

        # Apply custom priority rules
        custom_rules = self.preferences.get('priority_rules', {})
        for rule in custom_rules:
            if self._matches_rule(email, rule):
                ai_classification['priority'] = rule['priority']
                ai_classification['category'] = rule.get('category', ai_classification['category'])

        # Keyword-based priority boost
        subject_lower = email['subject'].lower()
        for priority, keywords in self.priority_keywords.items():
            if any(kw in subject_lower for kw in keywords):
                if self._priority_level(priority) > self._priority_level(ai_classification['priority']):
                    ai_classification['priority'] = priority

        return ai_classification

    def _matches_rule(self, email: dict, rule: dict) -> bool:
        """Check if email matches custom rule conditions"""
        if 'sender_pattern' in rule:
            if not re.search(rule['sender_pattern'], email['sender_email']):
                return False

        if 'subject_contains' in rule:
            if rule['subject_contains'].lower() not in email['subject'].lower():
                return False

        return True

    def _priority_level(self, priority: str) -> int:
        """Convert priority to numeric level for comparison"""
        levels = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        return levels.get(priority, 2)
```

### Phase 4: Response Generation (Week 4)

#### 4.1 Response Generator Service
```python
# backend/app/services/response_generator.py
from openai import OpenAI
from typing import Optional

class ResponseGenerator:
    def __init__(self):
        self.client = OpenAI()

    def generate_response(
        self,
        email_subject: str,
        email_body: str,
        tone: str = "professional",
        length: str = "medium",
        context: Optional[str] = None
    ) -> dict:
        """Generate email response using OpenAI"""

        system_prompt = self._build_system_prompt(tone, length)
        user_prompt = self._build_user_prompt(email_subject, email_body, context)

        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        generated_text = response.choices[0].message.content

        return {
            'response_text': generated_text,
            'tone': tone,
            'length': length,
            'model_used': 'gpt-4-turbo-preview',
            'tokens_used': response.usage.total_tokens
        }

    def _build_system_prompt(self, tone: str, length: str) -> str:
        """Build system prompt based on preferences"""

        tone_instructions = {
            'professional': 'formal, respectful, and business-appropriate',
            'casual': 'friendly, conversational, and relaxed',
            'formal': 'very formal, strictly professional, and polished',
            'concise': 'brief, to-the-point, and efficient'
        }

        length_instructions = {
            'short': '2-3 sentences maximum',
            'medium': '1 short paragraph (4-6 sentences)',
            'long': '2-3 paragraphs with detailed explanation'
        }

        return f"""You are an expert email response assistant. Generate {tone_instructions.get(tone, 'professional')}
        email responses. Keep responses {length_instructions.get(length, 'medium')}.

        Guidelines:
        - Be clear and actionable
        - Address the main points from the original email
        - Use appropriate greetings and closings
        - Maintain consistency with the requested tone
        - Do not include subject lines
        """

    def _build_user_prompt(self, subject: str, body: str, context: Optional[str]) -> str:
        """Build user prompt with email content"""

        prompt = f"""Generate a response to the following email:

        Subject: {subject}

        Email Content:
        {body[:1500]}
        """

        if context:
            prompt += f"\n\nAdditional Context:\n{context}"

        return prompt

    def generate_multiple_options(
        self,
        email_subject: str,
        email_body: str,
        num_options: int = 3
    ) -> list[dict]:
        """Generate multiple response options with different tones"""

        tones = ['professional', 'casual', 'concise']
        responses = []

        for tone in tones[:num_options]:
            response = self.generate_response(email_subject, email_body, tone=tone)
            responses.append(response)

        return responses
```

#### 4.2 Response Templates
```python
# backend/app/services/template_service.py
from typing import Dict, List

class TemplateService:
    def __init__(self):
        self.templates = {
            'acknowledgment': """
                Thank you for your email. I've received your message regarding {topic}
                and will review it carefully. I'll get back to you within {timeframe}.
            """,
            'meeting_request': """
                Thank you for reaching out. I'd be happy to schedule a meeting to discuss {topic}.
                I'm available {availability}. Please let me know what works best for you.
            """,
            'information_request': """
                Thank you for your inquiry about {topic}. Here's the information you requested:

                {information}

                Please let me know if you need any additional details.
            """,
            'decline_politely': """
                Thank you for thinking of me regarding {topic}. Unfortunately, I won't be able to
                {action} at this time due to {reason}. I appreciate your understanding.
            """,
            'follow_up': """
                I wanted to follow up on {topic}. {update}

                Please let me know if you have any questions or need further information.
            """
        }

    def get_template(self, template_name: str) -> str:
        """Retrieve template by name"""
        return self.templates.get(template_name, '')

    def fill_template(self, template_name: str, variables: Dict[str, str]) -> str:
        """Fill template with provided variables"""
        template = self.get_template(template_name)
        return template.format(**variables)
```

### Phase 5: Frontend Development (Week 5-6)

#### 5.1 Email Dashboard Component
```typescript
// frontend/app/dashboard/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { EmailList } from '@/components/EmailList';
import { TriageQueue } from '@/components/TriageQueue';
import { Stats } from '@/components/Stats';

interface Email {
  id: string;
  subject: string;
  sender: string;
  receivedAt: string;
  category: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  urgencyScore: number;
  requiresAction: boolean;
}

export default function Dashboard() {
  const { data: emails, isLoading } = useQuery<Email[]>({
    queryKey: ['emails'],
    queryFn: async () => {
      const response = await fetch('/api/v1/emails');
      return response.json();
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await fetch('/api/v1/emails/stats');
      return response.json();
    },
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Email Dashboard</h1>

      <Stats data={stats} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <div className="lg:col-span-2">
          <EmailList emails={emails} isLoading={isLoading} />
        </div>

        <div>
          <TriageQueue emails={emails?.filter(e => e.requiresAction)} />
        </div>
      </div>
    </div>
  );
}
```

#### 5.2 Response Editor Component
```typescript
// frontend/components/ResponseEditor.tsx
'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

interface ResponseEditorProps {
  emailId: string;
  originalEmail: {
    subject: string;
    body: string;
    sender: string;
  };
  onSend: () => void;
}

export function ResponseEditor({ emailId, originalEmail, onSend }: ResponseEditorProps) {
  const [response, setResponse] = useState('');
  const [tone, setTone] = useState<'professional' | 'casual' | 'formal'>('professional');
  const [isEditing, setIsEditing] = useState(false);

  const generateMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/v1/responses/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_id: emailId,
          tone,
          length: 'medium',
        }),
      });
      return res.json();
    },
    onSuccess: (data) => {
      setResponse(data.response_text);
      setIsEditing(true);
    },
  });

  const sendMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/v1/responses/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_id: emailId,
          response_text: response,
        }),
      });
      return res.json();
    },
    onSuccess: () => {
      onSend();
    },
  });

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Original Email</h3>
        <div className="bg-gray-50 p-4 rounded">
          <p className="text-sm text-gray-600">From: {originalEmail.sender}</p>
          <p className="text-sm font-medium mt-1">Subject: {originalEmail.subject}</p>
          <p className="text-sm mt-2 whitespace-pre-wrap">{originalEmail.body.substring(0, 200)}...</p>
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">Response Tone</label>
        <select
          value={tone}
          onChange={(e) => setTone(e.target.value as any)}
          className="w-full border rounded px-3 py-2"
        >
          <option value="professional">Professional</option>
          <option value="casual">Casual</option>
          <option value="formal">Formal</option>
        </select>
      </div>

      {!isEditing ? (
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {generateMutation.isPending ? 'Generating...' : 'Generate Response'}
        </button>
      ) : (
        <>
          <textarea
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            rows={10}
            className="w-full border rounded px-3 py-2 mb-4"
            placeholder="Edit your response..."
          />

          <div className="flex gap-2">
            <button
              onClick={() => generateMutation.mutate()}
              className="flex-1 bg-gray-200 py-2 rounded hover:bg-gray-300"
            >
              Regenerate
            </button>
            <button
              onClick={() => sendMutation.mutate()}
              disabled={sendMutation.isPending}
              className="flex-1 bg-green-600 text-white py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {sendMutation.isPending ? 'Sending...' : 'Send Email'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
```

#### 5.3 Triage Queue Component
```typescript
// frontend/components/TriageQueue.tsx
'use client';

import { useMemo } from 'react';

interface Email {
  id: string;
  subject: string;
  sender: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  category: string;
  urgencyScore: number;
}

interface TriageQueueProps {
  emails?: Email[];
}

const priorityColors = {
  urgent: 'bg-red-100 border-red-500 text-red-800',
  high: 'bg-orange-100 border-orange-500 text-orange-800',
  medium: 'bg-yellow-100 border-yellow-500 text-yellow-800',
  low: 'bg-green-100 border-green-500 text-green-800',
};

export function TriageQueue({ emails = [] }: TriageQueueProps) {
  const sortedEmails = useMemo(() => {
    return [...emails].sort((a, b) => b.urgencyScore - a.urgencyScore);
  }, [emails]);

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h2 className="text-xl font-bold mb-4">Action Required</h2>

      {sortedEmails.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No emails require action</p>
      ) : (
        <div className="space-y-3">
          {sortedEmails.map((email) => (
            <div
              key={email.id}
              className={`border-l-4 p-3 rounded ${priorityColors[email.priority]}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="font-medium text-sm truncate">{email.subject}</p>
                  <p className="text-xs mt-1 opacity-75">{email.sender}</p>
                </div>
                <span className="text-xs font-semibold ml-2">{email.priority.toUpperCase()}</span>
              </div>
              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs bg-white bg-opacity-50 px-2 py-1 rounded">
                  {email.category}
                </span>
                <div className="flex-1 bg-white bg-opacity-30 rounded-full h-1">
                  <div
                    className="bg-current h-full rounded-full"
                    style={{ width: `${email.urgencyScore * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Phase 6: API Endpoints (Week 6)

#### 6.1 Email Endpoints
```python
# backend/app/api/v1/emails.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.email import EmailResponse, EmailStats
from app.models.email import Email
from app.services.email_service import EmailService

router = APIRouter()

@router.get("/", response_model=List[EmailResponse])
async def get_emails(
    skip: int = 0,
    limit: int = 50,
    category: str = None,
    priority: str = None,
    db: Session = Depends(get_db)
):
    """Get list of emails with optional filters"""
    query = db.query(Email)

    if category:
        query = query.filter(Email.category == category)

    if priority:
        query = query.filter(Email.priority == priority)

    emails = query.order_by(Email.received_at.desc()).offset(skip).limit(limit).all()
    return emails

@router.get("/stats", response_model=EmailStats)
async def get_email_stats(db: Session = Depends(get_db)):
    """Get email statistics"""
    total_emails = db.query(Email).count()
    unread_count = db.query(Email).filter(Email.processed_at.is_(None)).count()

    category_counts = db.query(
        Email.category,
        func.count(Email.id)
    ).group_by(Email.category).all()

    priority_counts = db.query(
        Email.priority,
        func.count(Email.id)
    ).group_by(Email.priority).all()

    return {
        'total_emails': total_emails,
        'unread_count': unread_count,
        'categories': dict(category_counts),
        'priorities': dict(priority_counts)
    }

@router.post("/sync")
async def sync_emails(db: Session = Depends(get_db)):
    """Trigger email sync from provider"""
    # Queue background task to fetch new emails
    from app.workers.email_processor import fetch_new_emails
    task = fetch_new_emails.delay()

    return {'task_id': task.id, 'status': 'queued'}

@router.put("/{email_id}/classify")
async def reclassify_email(
    email_id: str,
    category: str,
    priority: str,
    db: Session = Depends(get_db)
):
    """Manually reclassify an email (for feedback/learning)"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email.category = category
    email.priority = priority
    db.commit()

    # Store feedback for model improvement
    from app.services.feedback_service import FeedbackService
    feedback_service = FeedbackService()
    feedback_service.record_classification_feedback(
        email_id=email_id,
        corrected_category=category,
        corrected_priority=priority
    )

    return {'status': 'updated'}
```

#### 6.2 Response Generation Endpoints
```python
# backend/app/api/v1/responses.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.response import ResponseRequest, ResponseGenerated
from app.services.response_generator import ResponseGenerator
from app.models.email import Email
from app.models.generated_response import GeneratedResponse

router = APIRouter()

@router.post("/generate", response_model=ResponseGenerated)
async def generate_response(
    request: ResponseRequest,
    db: Session = Depends(get_db)
):
    """Generate AI response for an email"""
    email = db.query(Email).filter(Email.id == request.email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    generator = ResponseGenerator()
    response_data = generator.generate_response(
        email_subject=email.subject,
        email_body=email.body_text,
        tone=request.tone,
        length=request.length,
        context=request.context
    )

    # Save generated response
    generated_response = GeneratedResponse(
        email_id=email.id,
        response_text=response_data['response_text'],
        tone=response_data['tone'],
        length=response_data['length'],
        model_used=response_data['model_used']
    )

    db.add(generated_response)
    db.commit()
    db.refresh(generated_response)

    return generated_response

@router.post("/send")
async def send_response(
    email_id: str,
    response_text: str,
    db: Session = Depends(get_db)
):
    """Send generated response via email"""
    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Send email via Gmail API
    from app.services.email_service import EmailService
    email_service = EmailService(user_credentials={})  # Get from session

    email_service.send_reply(
        message_id=email.message_id,
        reply_text=response_text
    )

    # Update response record
    response = db.query(GeneratedResponse).filter(
        GeneratedResponse.email_id == email_id
    ).order_by(GeneratedResponse.generation_timestamp.desc()).first()

    if response:
        response.sent_at = func.now()
        response.user_approved = True
        db.commit()

    return {'status': 'sent'}

@router.get("/{email_id}/history")
async def get_response_history(
    email_id: str,
    db: Session = Depends(get_db)
):
    """Get all generated responses for an email"""
    responses = db.query(GeneratedResponse).filter(
        GeneratedResponse.email_id == email_id
    ).order_by(GeneratedResponse.generation_timestamp.desc()).all()

    return responses
```

### Phase 7: Testing & Quality Assurance (Week 7)

#### 7.1 Backend Unit Tests
```python
# backend/tests/test_triage_service.py
import pytest
from app.services.triage_service import TriageService

@pytest.fixture
def triage_service():
    return TriageService()

def test_classify_urgent_email(triage_service):
    """Test classification of urgent email"""
    result = triage_service.classify_email(
        subject="URGENT: Server Down",
        body="Our production server is not responding. Need immediate attention.",
        sender="ops@company.com"
    )

    assert result['priority'] in ['urgent', 'high']
    assert result['requires_action'] is True
    assert result['urgency_score'] > 0.7

def test_classify_marketing_email(triage_service):
    """Test classification of marketing email"""
    result = triage_service.classify_email(
        subject="Special Offer: 50% Off",
        body="Don't miss our amazing sale this weekend!",
        sender="marketing@store.com"
    )

    assert result['category'] == 'marketing'
    assert result['priority'] == 'low'
    assert result['requires_action'] is False

def test_classify_meeting_request(triage_service):
    """Test classification of meeting request"""
    result = triage_service.classify_email(
        subject="Meeting Request for Project Review",
        body="Can we schedule a meeting to discuss the project status?",
        sender="manager@company.com"
    )

    assert result['category'] in ['work', 'support']
    assert result['requires_action'] is True
```

#### 7.2 API Integration Tests
```python
# backend/tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_emails():
    """Test email list endpoint"""
    response = client.get("/api/v1/emails/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_generate_response():
    """Test response generation endpoint"""
    payload = {
        "email_id": "test-email-id",
        "tone": "professional",
        "length": "medium"
    }

    response = client.post("/api/v1/responses/generate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert 'response_text' in data
    assert 'tone' in data
    assert data['tone'] == 'professional'

def test_email_stats():
    """Test email statistics endpoint"""
    response = client.get("/api/v1/emails/stats")
    assert response.status_code == 200

    data = response.json()
    assert 'total_emails' in data
    assert 'categories' in data
    assert 'priorities' in data
```

#### 7.3 Frontend Component Tests
```typescript
// frontend/__tests__/ResponseEditor.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ResponseEditor } from '@/components/ResponseEditor';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

describe('ResponseEditor', () => {
  const mockEmail = {
    subject: 'Test Subject',
    body: 'Test email body',
    sender: 'test@example.com',
  };

  it('renders original email content', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ResponseEditor
          emailId="123"
          originalEmail={mockEmail}
          onSend={() => {}}
        />
      </QueryClientProvider>
    );

    expect(screen.getByText(/Test Subject/i)).toBeInTheDocument();
    expect(screen.getByText(/test@example.com/i)).toBeInTheDocument();
  });

  it('generates response when button clicked', async () => {
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <ResponseEditor
          emailId="123"
          originalEmail={mockEmail}
          onSend={() => {}}
        />
      </QueryClientProvider>
    );

    const generateButton = screen.getByText(/Generate Response/i);
    await user.click(generateButton);

    await waitFor(() => {
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });
  });
});
```

### Phase 8: Deployment & Production (Week 8)

#### 8.1 Environment Configuration
```bash
# .env.production
# Database
DATABASE_URL=postgresql://user:password@db-host:5432/email_triage

# Redis
REDIS_URL=redis://redis-host:6379

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# Gmail OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback

# Security
SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# App Configuration
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com
```

#### 8.2 Production Docker Configuration
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    restart: always

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
```

## Potential Challenges & Solutions

### Challenge 1: Email Provider API Rate Limits
**Solution:**
- Implement exponential backoff retry logic
- Use webhook notifications instead of polling when available
- Cache email data to minimize API calls
- Implement request queuing with Celery

### Challenge 2: OpenAI API Costs
**Solution:**
- Cache common classification results using embeddings
- Use GPT-3.5-turbo for simple classifications
- Reserve GPT-4 for complex response generation only
- Implement token usage monitoring and budget alerts
- Consider fine-tuning smaller models for classification

### Challenge 3: Real-time Email Synchronization
**Solution:**
- Use Gmail Push Notifications (Pub/Sub) instead of polling
- Implement WebSocket connections for real-time UI updates
- Use Redis for caching frequently accessed data
- Background workers for processing queue

### Challenge 4: Data Privacy & Security
**Solution:**
- Encrypt sensitive data at rest using database-level encryption
- Use OAuth 2.0 with secure token storage
- Implement row-level security in PostgreSQL
- Never log email content or personal information
- Provide data export and deletion capabilities (GDPR compliance)

### Challenge 5: Response Quality & Accuracy
**Solution:**
- Implement user feedback loop for continuous improvement
- A/B test different prompts and models
- Store successful responses as examples for few-shot learning
- Allow users to create custom response templates
- Implement confidence scores and suggest review when low

### Challenge 6: Scalability
**Solution:**
- Horizontal scaling with load balancers
- Database read replicas for queries
- Separate processing queues by priority
- CDN for frontend assets
- Connection pooling for database

## Testing Strategy

### Unit Tests (80%+ Coverage Target)
- Triage service classification logic
- Response generation functions
- Priority engine rule matching
- Email parsing and formatting
- API endpoint request/response handling

### Integration Tests
- End-to-end email processing flow
- Database operations and transactions
- OpenAI API integration
- Gmail API integration
- Celery task execution

### E2E Tests (Playwright)
- User authentication flow
- Email dashboard interaction
- Response generation and editing
- Settings and preferences management
- Mobile responsive behavior

### Performance Tests
- Load testing with 1000+ emails
- Concurrent user simulation
- API response time benchmarks
- Database query optimization
- Memory leak detection

## Success Criteria

### Functional Requirements
✅ Successfully authenticate with Gmail OAuth
✅ Fetch and store emails from Gmail
✅ Classify emails with 85%+ accuracy
✅ Generate contextually appropriate responses
✅ Allow human review and editing before sending
✅ Learn from user feedback and corrections

### Performance Requirements
✅ Process new email within 30 seconds
✅ Generate response in under 5 seconds
✅ Support 100+ emails per user
✅ Handle 50+ concurrent users
✅ API response time < 200ms (95th percentile)

### User Experience Requirements
✅ Intuitive, clean interface
✅ Mobile-responsive design
✅ Real-time updates without page refresh
✅ Clear priority and category visual indicators
✅ One-click response generation
✅ Easy response editing and customization

## Future Enhancements (Post-MVP)

1. **Multi-provider Support**: Outlook, Yahoo Mail integration
2. **Advanced Analytics**: Email patterns, response time tracking, sentiment trends
3. **Calendar Integration**: Auto-schedule meetings from email requests
4. **Smart Attachments**: AI-powered attachment analysis and summarization
5. **Bulk Operations**: Process multiple emails simultaneously
6. **Mobile App**: Native iOS and Android applications
7. **Voice Responses**: Generate responses via voice commands
8. **Multi-language Support**: Detect and respond in multiple languages
9. **Team Collaboration**: Shared inboxes and delegation
10. **Custom AI Models**: Fine-tune models on user's writing style

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Project Setup | Docker environment, database schema, project structure |
| 2 | Email Integration | Gmail OAuth, email fetching, data pipeline |
| 3 | AI Triage | Classification service, priority engine, embeddings |
| 4 | Response Generation | OpenAI integration, templates, multi-option generation |
| 5-6 | Frontend | Dashboard, response editor, triage queue, settings |
| 6 | API Development | REST endpoints, authentication, error handling |
| 7 | Testing | Unit tests, integration tests, E2E tests |
| 8 | Deployment | Production configuration, monitoring, documentation |

## Getting Started

```bash
# Clone repository
git clone <repository-url>
cd email-auto-organizer

# Setup environment
cp .env.example .env
# Edit .env with your credentials

# Start development environment
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Conclusion

This implementation plan provides a comprehensive roadmap for building a Smart Email Triage & Response Generator. The architecture leverages modern technologies (Next.js, FastAPI, OpenAI) to create an intelligent system that reduces email management overhead while maintaining professional communication standards.

Key success factors:
- Iterative development with user feedback
- Focus on accuracy and user trust
- Performance optimization from day one
- Privacy and security by design
- Scalable architecture for growth

The phased approach allows for early validation and continuous improvement, ensuring the final product meets real user needs effectively.
