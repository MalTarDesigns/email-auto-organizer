# AI Triage Engine Usage Examples

This directory contains example code for using the Phase 3 AI Triage Engine services.

## Quick Start

### 1. Basic Classification

```python
from app.services import TriageService

triage = TriageService()
result = triage.classify_email(
    subject="Urgent: Server Down",
    body="Production server is experiencing issues",
    sender="ops@company.com"
)

print(result['category'])  # work
print(result['priority'])  # urgent
```

### 2. Custom Priority Rules

```python
from app.services import PriorityEngine

preferences = {
    'whitelist_senders': ['boss@company.com'],
    'blacklist_senders': ['spam@example.com'],
    'priority_rules': [
        {
            'sender_pattern': r'.*@vip\.com',
            'priority': 'urgent',
            'category': 'work'
        }
    ]
}

engine = PriorityEngine(preferences)
final = engine.apply_custom_rules(email_dict, ai_classification)
```

### 3. Complete Pipeline

```python
from app.services import CompleteTriageService

triage = CompleteTriageService()
result = await triage.process_email(email_object, user_preferences)

print(result['classification'])
print(result['confidence'])
print(result['requires_review'])
print(result['similar_emails'])
```

## Running Examples

```bash
# Set up environment
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Run examples
python examples/triage_usage_example.py
```

## Available Examples

1. **Basic Classification** - Simple email classification using AI
2. **Custom Rules** - Apply user-defined priority rules
3. **Semantic Search** - Generate embeddings and find similar emails
4. **Confidence Calculation** - Calculate and interpret confidence scores
5. **Complete Triage** - End-to-end triage pipeline
6. **Batch Processing** - Process multiple emails efficiently
7. **Error Handling** - Handle edge cases and errors gracefully

## User Preferences Schema

```python
{
    'whitelist_senders': [
        'boss@company.com',
        'client@vip.com'
    ],
    'blacklist_senders': [
        'newsletter@marketing.com',
        'spam@example.com'
    ],
    'priority_rules': [
        {
            'sender_pattern': r'.*@important-domain\.com',
            'subject_contains': 'urgent',
            'priority': 'high',
            'category': 'work'
        }
    ]
}
```

## Classification Output

```python
{
    'classification': {
        'category': 'work',           # work, personal, marketing, support, finance, other
        'priority': 'high',           # urgent, high, medium, low
        'urgency_score': 0.8,         # 0.0 to 1.0
        'sentiment': 'neutral',       # positive, neutral, negative
        'requires_action': True,      # boolean
        'reasoning': 'Explanation'    # AI reasoning
    },
    'confidence': 0.85,               # 0.0 to 1.0
    'requires_review': False,         # True if confidence < 0.6
    'similar_emails': ['uuid1', ...]  # List of similar email IDs
}
```

## Testing

```bash
# Run unit tests
pytest tests/services/test_triage_service.py -v

# Run integration tests
pytest tests/integration/test_complete_triage.py -v

# Run with coverage
pytest --cov=app.services tests/services/ -v
```

## Troubleshooting

### OpenAI API Errors
- Verify API key is set: `echo $OPENAI_API_KEY`
- Check API quota and billing
- Review rate limits

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure pgvector extension is installed

### Import Errors
- Activate virtual environment
- Install dependencies: `pip install -r requirements.txt`
- Check Python version (3.11+ recommended)

## Performance Tips

1. **Batch Processing**: Process multiple emails in parallel
2. **Caching**: Cache embeddings for frequently accessed emails
3. **Index Optimization**: Ensure pgvector index is created
4. **Text Truncation**: Limit body text to reduce API costs
5. **Temperature**: Lower temperature (0.3) for consistent results

## Best Practices

1. **Error Handling**: Always wrap triage calls in try-except blocks
2. **User Preferences**: Store preferences in user model, not hardcoded
3. **Confidence Thresholds**: Adjust review threshold based on your needs
4. **Logging**: Log classification results for analysis and improvement
5. **Testing**: Test with diverse email samples before production use

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Phase 3 Specification](../../specs/phases/phase-03-ai-triage.md)
- [Implementation Summary](../../PHASE_3_IMPLEMENTATION.md)
