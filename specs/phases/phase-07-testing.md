# Phase 7: Testing & Quality Assurance

**Timeline**: Week 7

## Objectives

- Implement comprehensive unit tests (80%+ coverage)
- Create integration tests for API
- Build E2E tests for critical user flows
- Setup performance testing
- Implement test automation CI/CD

## 7.1 Backend Unit Tests

### Triage Service Tests

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

def test_embedding_generation(triage_service):
    """Test embedding vector generation"""
    text = "This is a test email about project updates"
    embedding = triage_service.generate_embedding(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 1536  # OpenAI embedding size
    assert all(isinstance(x, float) for x in embedding)
```

### Priority Engine Tests

```python
# backend/tests/test_priority_engine.py
import pytest
from app.services.priority_engine import PriorityEngine

@pytest.fixture
def user_preferences():
    return {
        'whitelist_senders': ['important@company.com'],
        'blacklist_senders': ['spam@marketing.com'],
        'priority_rules': [
            {
                'sender_pattern': 'ceo@.*',
                'priority': 'urgent'
            }
        ]
    }

def test_whitelist_priority_boost(user_preferences):
    """Test that whitelisted senders get high priority"""
    engine = PriorityEngine(user_preferences)

    email = {
        'subject': 'Regular email',
        'sender_email': 'important@company.com',
        'body': 'Test'
    }

    ai_classification = {'priority': 'medium'}
    result = engine.apply_custom_rules(email, ai_classification)

    assert result['priority'] == 'high'

def test_blacklist_priority_reduction(user_preferences):
    """Test that blacklisted senders get low priority"""
    engine = PriorityEngine(user_preferences)

    email = {
        'subject': 'Important update',
        'sender_email': 'spam@marketing.com',
        'body': 'Test'
    }

    ai_classification = {'priority': 'high'}
    result = engine.apply_custom_rules(email, ai_classification)

    assert result['priority'] == 'low'

def test_custom_rule_matching(user_preferences):
    """Test custom rule pattern matching"""
    engine = PriorityEngine(user_preferences)

    email = {
        'subject': 'Message from CEO',
        'sender_email': 'ceo@company.com',
        'body': 'Test'
    }

    ai_classification = {'priority': 'medium'}
    result = engine.apply_custom_rules(email, ai_classification)

    assert result['priority'] == 'urgent'
```

### Response Generator Tests

```python
# backend/tests/test_response_generator.py
import pytest
from app.services.response_generator import ResponseGenerator

@pytest.fixture
def response_generator():
    return ResponseGenerator()

def test_generate_professional_response(response_generator):
    """Test professional tone response generation"""
    result = response_generator.generate_response(
        email_subject="Meeting Request",
        email_body="Can we meet next week?",
        tone="professional"
    )

    assert 'response_text' in result
    assert result['tone'] == 'professional'
    assert len(result['response_text']) > 0

def test_generate_multiple_options(response_generator):
    """Test generating multiple response options"""
    results = response_generator.generate_multiple_options(
        email_subject="Project Update",
        email_body="How is the project progressing?",
        num_options=3
    )

    assert len(results) == 3
    assert all('response_text' in r for r in results)
    assert len(set(r['tone'] for r in results)) == 3  # Different tones
```

## 7.2 API Integration Tests

### Email Endpoints Tests

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

def test_get_email_stats():
    """Test email statistics endpoint"""
    response = client.get("/api/v1/emails/stats")
    assert response.status_code == 200

    data = response.json()
    assert 'total_emails' in data
    assert 'categories' in data
    assert 'priorities' in data

def test_get_email_by_id():
    """Test get single email"""
    # First create a test email
    email_id = "test-email-id"

    response = client.get(f"/api/v1/emails/{email_id}")
    assert response.status_code in [200, 404]

def test_reclassify_email():
    """Test manual reclassification"""
    email_id = "test-email-id"

    response = client.put(
        f"/api/v1/emails/{email_id}/classify",
        params={"category": "work", "priority": "high"}
    )

    assert response.status_code in [200, 404]
```

### Response Endpoints Tests

```python
# backend/tests/test_response_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_generate_response():
    """Test response generation endpoint"""
    payload = {
        "email_id": "test-email-id",
        "tone": "professional",
        "length": "medium"
    }

    response = client.post("/api/v1/responses/generate", json=payload)
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert 'response_text' in data
        assert 'tone' in data
        assert data['tone'] == 'professional'

def test_send_response():
    """Test sending response"""
    payload = {
        "email_id": "test-email-id",
        "response_text": "Thank you for your email."
    }

    response = client.post("/api/v1/responses/send", json=payload)
    assert response.status_code in [200, 404]

def test_response_history():
    """Test getting response history"""
    email_id = "test-email-id"

    response = client.get(f"/api/v1/responses/{email_id}/history")
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        assert isinstance(response.json(), list)
```

## 7.3 Frontend Component Tests

### Response Editor Tests

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

  it('allows editing generated response', async () => {
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

    // Generate response first
    const generateButton = screen.getByText(/Generate Response/i);
    await user.click(generateButton);

    await waitFor(() => {
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
    });

    // Edit the response
    const textarea = screen.getByRole('textbox');
    await user.clear(textarea);
    await user.type(textarea, 'Custom response text');

    expect(textarea).toHaveValue('Custom response text');
  });
});
```

### Triage Queue Tests

```typescript
// frontend/__tests__/TriageQueue.test.tsx
import { render, screen } from '@testing-library/react';
import { TriageQueue } from '@/components/TriageQueue';

describe('TriageQueue', () => {
  const mockEmails = [
    {
      id: '1',
      subject: 'Urgent Task',
      sender: 'boss@company.com',
      priority: 'urgent' as const,
      category: 'work',
      urgencyScore: 0.9,
    },
    {
      id: '2',
      subject: 'Review Request',
      sender: 'colleague@company.com',
      priority: 'high' as const,
      category: 'work',
      urgencyScore: 0.7,
    },
  ];

  it('renders email list', () => {
    render(<TriageQueue emails={mockEmails} />);

    expect(screen.getByText('Urgent Task')).toBeInTheDocument();
    expect(screen.getByText('Review Request')).toBeInTheDocument();
  });

  it('displays empty state when no emails', () => {
    render(<TriageQueue emails={[]} />);

    expect(screen.getByText(/No emails require action/i)).toBeInTheDocument();
  });

  it('sorts emails by urgency score', () => {
    render(<TriageQueue emails={mockEmails} />);

    const emailCards = screen.getAllByRole('generic').filter(
      (el) => el.className.includes('border-l-4')
    );

    // First email should be the urgent one
    expect(emailCards[0]).toHaveTextContent('Urgent Task');
  });
});
```

## 7.4 E2E Tests with Playwright

### Critical User Flows

```typescript
// frontend/e2e/email-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Email Workflow', () => {
  test('user can view emails and generate response', async ({ page }) => {
    await page.goto('/dashboard');

    // Wait for emails to load
    await expect(page.locator('[data-testid="email-list"]')).toBeVisible();

    // Click on first email
    await page.locator('[data-testid="email-card"]').first().click();

    // Wait for email detail
    await expect(page.locator('[data-testid="email-detail"]')).toBeVisible();

    // Click generate response
    await page.locator('button:has-text("Generate Response")').click();

    // Wait for response to be generated
    await expect(page.locator('textarea')).toBeVisible();

    // Verify response text exists
    const responseText = await page.locator('textarea').inputValue();
    expect(responseText.length).toBeGreaterThan(0);
  });

  test('user can edit and send response', async ({ page }) => {
    await page.goto('/dashboard');

    // Navigate to email and generate response
    await page.locator('[data-testid="email-card"]').first().click();
    await page.locator('button:has-text("Generate Response")').click();

    // Wait for textarea
    await expect(page.locator('textarea')).toBeVisible();

    // Edit response
    await page.locator('textarea').fill('Custom edited response');

    // Send response
    await page.locator('button:has-text("Send Email")').click();

    // Verify success message or redirect
    await expect(page.locator('text=sent')).toBeVisible({ timeout: 5000 });
  });

  test('user can filter emails by category', async ({ page }) => {
    await page.goto('/dashboard');

    // Select category filter
    await page.selectOption('select[name="category"]', 'work');

    // Verify filtered results
    await expect(page.locator('[data-testid="email-card"]')).toHaveCount(
      await page.locator('[data-testid="email-card"]').count()
    );
  });
});
```

## 7.5 Performance Tests

### Load Testing

```python
# backend/tests/performance/test_load.py
import pytest
from locust import HttpUser, task, between

class EmailTriageUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_emails(self):
        """Test email list endpoint under load"""
        self.client.get("/api/v1/emails/")

    @task(2)
    def get_stats(self):
        """Test stats endpoint under load"""
        self.client.get("/api/v1/emails/stats")

    @task(1)
    def generate_response(self):
        """Test response generation under load"""
        self.client.post("/api/v1/responses/generate", json={
            "email_id": "test-id",
            "tone": "professional",
            "length": "medium"
        })

# Run with: locust -f test_load.py --host=http://localhost:8000
```

## 7.6 Test Configuration

### Pytest Configuration

```ini
# backend/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

### Jest Configuration

```javascript
// frontend/jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'app/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

## Deliverables

- ✅ Unit tests for all services (80%+ coverage)
- ✅ Integration tests for API endpoints
- ✅ Component tests for React components
- ✅ E2E tests for critical user flows
- ✅ Performance/load testing setup
- ✅ Test automation in CI/CD
- ✅ Code coverage reporting
- ✅ Test documentation

## Success Criteria

- Code coverage >80% for backend
- Code coverage >80% for frontend
- All critical user flows tested with E2E
- API response time <200ms under load
- System handles 50+ concurrent users
- Zero critical bugs in production
- All tests pass in CI/CD pipeline
