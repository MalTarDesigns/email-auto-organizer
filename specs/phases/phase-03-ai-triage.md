# Phase 3: AI Triage Engine

**Timeline**: Week 3

## Objectives

- Implement email classification service using OpenAI
- Build priority rules engine
- Create embedding generation for semantic search
- Develop custom rule application system
- Setup confidence scoring mechanism

## 3.1 Email Classification Service

### Triage Service

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

## 3.2 Priority Rules Engine

### Custom Priority Logic

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

## 3.3 Semantic Search with Embeddings

### Embedding Service

```python
# backend/app/services/embedding_service.py
from openai import OpenAI
from sqlalchemy import func
from app.models.email import Email
from app.core.database import SessionLocal

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI()

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text"""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]  # Limit text length
        )
        return response.data[0].embedding

    def embed_email(self, email: Email) -> list[float]:
        """Generate embedding for email content"""
        # Combine subject and body for embedding
        content = f"{email.subject} {email.body_text[:1000]}"
        return self.generate_embedding(content)

    def find_similar_emails(self, email_id: str, limit: int = 5) -> list:
        """Find similar emails using vector similarity"""
        db = SessionLocal()

        try:
            # Get target email
            target_email = db.query(Email).filter(Email.id == email_id).first()

            if not target_email or not target_email.embedding:
                return []

            # Find similar emails using cosine similarity
            similar_emails = db.query(Email).filter(
                Email.id != email_id,
                Email.embedding.isnot(None)
            ).order_by(
                func.cosine_distance(Email.embedding, target_email.embedding)
            ).limit(limit).all()

            return similar_emails

        finally:
            db.close()
```

## 3.4 Classification Confidence Scoring

### Confidence Calculation

```python
# backend/app/services/confidence_service.py
from typing import Dict

class ConfidenceService:
    def calculate_confidence(
        self,
        ai_classification: dict,
        user_rules_applied: bool,
        similar_emails: list
    ) -> float:
        """Calculate confidence score for classification"""

        confidence = 0.7  # Base confidence

        # Boost confidence if user rules were applied
        if user_rules_applied:
            confidence += 0.2

        # Boost confidence if similar emails have same classification
        if similar_emails:
            matching_classifications = sum(
                1 for email in similar_emails
                if email.category == ai_classification['category']
            )
            similarity_boost = (matching_classifications / len(similar_emails)) * 0.1
            confidence += similarity_boost

        # Cap at 1.0
        return min(confidence, 1.0)

    def should_require_review(self, confidence: float) -> bool:
        """Determine if classification requires human review"""
        return confidence < 0.6
```

## 3.5 Complete Triage Pipeline

### Integrated Triage Flow

```python
# backend/app/services/complete_triage.py
from app.services.triage_service import TriageService
from app.services.priority_engine import PriorityEngine
from app.services.embedding_service import EmbeddingService
from app.services.confidence_service import ConfidenceService
from app.models.email import Email
from app.models.email_classification import EmailClassification

class CompleteTriageService:
    def __init__(self):
        self.triage_service = TriageService()
        self.embedding_service = EmbeddingService()
        self.confidence_service = ConfidenceService()

    async def process_email(self, email: Email, user_preferences: dict) -> dict:
        """Complete triage pipeline for an email"""

        # Step 1: AI Classification
        ai_classification = self.triage_service.classify_email(
            subject=email.subject,
            body=email.body_text,
            sender=email.sender_email
        )

        # Step 2: Apply user rules
        priority_engine = PriorityEngine(user_preferences)
        final_classification = priority_engine.apply_custom_rules(
            {
                'subject': email.subject,
                'sender_email': email.sender_email,
                'body': email.body_text
            },
            ai_classification
        )

        # Step 3: Generate embedding
        embedding = self.embedding_service.embed_email(email)

        # Step 4: Find similar emails
        email.embedding = embedding
        similar_emails = self.embedding_service.find_similar_emails(str(email.id))

        # Step 5: Calculate confidence
        confidence = self.confidence_service.calculate_confidence(
            ai_classification=final_classification,
            user_rules_applied=True,
            similar_emails=similar_emails
        )

        # Step 6: Determine if review needed
        requires_review = self.confidence_service.should_require_review(confidence)

        return {
            'classification': final_classification,
            'confidence': confidence,
            'requires_review': requires_review,
            'similar_emails': [str(e.id) for e in similar_emails]
        }
```

## Deliverables

- ✅ OpenAI-based email classification service
- ✅ Priority rules engine with custom logic
- ✅ Embedding generation for semantic search
- ✅ Similar email detection
- ✅ Confidence scoring mechanism
- ✅ User preference integration
- ✅ Classification storage and tracking
- ✅ Review flagging system

## Success Criteria

- Classification accuracy >85% on test data
- Priority assignment matches user expectations
- Embedding generation successful for all emails
- Similar emails identified correctly
- Confidence scores correlate with accuracy
- Custom rules properly override AI classifications
- Classification completes within 3 seconds per email
