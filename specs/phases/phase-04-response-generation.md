# Phase 4: Response Generation

**Timeline**: Week 4

## Objectives

- Implement AI-powered response generation
- Create response templates system
- Build multi-option generation
- Develop tone and style customization
- Setup response tracking and feedback

## 4.1 Response Generator Service

### Core Response Generation

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

## 4.2 Response Templates

### Template Service

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

    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.templates.keys())

    def add_custom_template(self, name: str, template: str):
        """Add user-defined custom template"""
        self.templates[name] = template

    def suggest_template(self, email_category: str, email_body: str) -> str:
        """Suggest appropriate template based on email content"""
        # Simple keyword-based template suggestion
        body_lower = email_body.lower()

        if 'meeting' in body_lower or 'schedule' in body_lower:
            return 'meeting_request'
        elif 'information' in body_lower or 'details' in body_lower:
            return 'information_request'
        elif 'follow up' in body_lower or 'following up' in body_lower:
            return 'follow_up'
        else:
            return 'acknowledgment'
```

## 4.3 Smart Response Enhancement

### Context-Aware Generation

```python
# backend/app/services/smart_response.py
from app.services.response_generator import ResponseGenerator
from app.services.template_service import TemplateService
from app.services.embedding_service import EmbeddingService

class SmartResponseService:
    def __init__(self):
        self.response_generator = ResponseGenerator()
        self.template_service = TemplateService()
        self.embedding_service = EmbeddingService()

    async def generate_smart_response(
        self,
        email: dict,
        user_preferences: dict,
        use_history: bool = True
    ) -> dict:
        """Generate response with historical context and learning"""

        # Find similar past emails
        context = ""
        if use_history:
            similar_emails = self.embedding_service.find_similar_emails(
                email['id'],
                limit=3
            )

            # Extract successful response patterns
            if similar_emails:
                context = self._build_historical_context(similar_emails)

        # Get user's preferred tone
        tone = user_preferences.get('response_tone', 'professional')
        length = user_preferences.get('response_length', 'medium')

        # Generate response
        response = self.response_generator.generate_response(
            email_subject=email['subject'],
            email_body=email['body'],
            tone=tone,
            length=length,
            context=context
        )

        return response

    def _build_historical_context(self, similar_emails: list) -> str:
        """Build context from similar historical emails"""
        context_parts = []

        for email in similar_emails:
            if email.responses and email.responses[0].user_approved:
                context_parts.append(
                    f"Similar email: {email.subject}\n"
                    f"Successful response: {email.responses[0].final_response[:200]}"
                )

        return "\n\n".join(context_parts)
```

## 4.4 Response Quality Scoring

### Quality Evaluation

```python
# backend/app/services/response_quality.py
from openai import OpenAI
import json

class ResponseQualityService:
    def __init__(self):
        self.client = OpenAI()

    def evaluate_response(
        self,
        original_email: str,
        generated_response: str
    ) -> dict:
        """Evaluate quality of generated response"""

        evaluation_prompt = f"""
        Evaluate the quality of this email response:

        Original Email:
        {original_email[:500]}

        Generated Response:
        {generated_response}

        Rate the response on the following criteria (0-10):
        1. Relevance - Does it address the email's main points?
        2. Professionalism - Is the tone appropriate?
        3. Clarity - Is it clear and easy to understand?
        4. Completeness - Does it fully respond to the email?
        5. Grammar - Is it grammatically correct?

        Provide scores and brief reasoning in JSON format.
        """

        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an email quality evaluator."},
                {"role": "user", "content": evaluation_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        evaluation = json.loads(response.choices[0].message.content)

        # Calculate overall score
        scores = [
            evaluation.get('relevance', 5),
            evaluation.get('professionalism', 5),
            evaluation.get('clarity', 5),
            evaluation.get('completeness', 5),
            evaluation.get('grammar', 5)
        ]
        overall_score = sum(scores) / len(scores)

        return {
            'overall_score': overall_score,
            'detailed_scores': evaluation,
            'should_regenerate': overall_score < 6
        }
```

## 4.5 Response Models

### Database Models

```python
# backend/app/models/generated_response.py
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class GeneratedResponse(Base):
    __tablename__ = "generated_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id = Column(UUID(as_uuid=True), ForeignKey('emails.id', ondelete='CASCADE'))
    response_text = Column(Text, nullable=False)
    tone = Column(String(50))
    length = Column(String(20))
    model_used = Column(String(50))
    generation_timestamp = Column(DateTime, server_default='now()')
    user_approved = Column(Boolean)
    user_edited = Column(Boolean, default=False)
    final_response = Column(Text)
    sent_at = Column(DateTime)
    feedback_score = Column(Integer)
    quality_score = Column(Numeric(3, 2))
    created_at = Column(DateTime, server_default='now()')

    # Relationships
    email = relationship("Email", back_populates="responses")
```

## Deliverables

- ✅ AI-powered response generation service
- ✅ Multiple tone options (professional, casual, formal, concise)
- ✅ Template system with common response patterns
- ✅ Multi-option generation
- ✅ Context-aware generation using history
- ✅ Response quality evaluation
- ✅ User preference integration
- ✅ Response tracking and storage

## Success Criteria

- Generate contextually appropriate responses
- Support multiple tone and length options
- Template suggestions match email type
- Quality scores >7/10 on average
- Response generation completes in <5 seconds
- Historical context improves response quality
- User edits tracked for learning
