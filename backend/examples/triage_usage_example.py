"""
Example usage of the AI Triage Engine services

This file demonstrates how to use the Phase 3 AI Triage services
for email classification, priority assignment, and semantic search.
"""

import asyncio
from app.services import (
    TriageService,
    PriorityEngine,
    EmbeddingService,
    ConfidenceService,
    CompleteTriageService
)
from app.models.email import Email
from app.core.database import SessionLocal


# Example 1: Basic Email Classification
async def example_basic_classification():
    """Classify a single email using AI"""

    triage_service = TriageService()

    result = triage_service.classify_email(
        subject="Urgent: Production server is down",
        body="We need immediate assistance with the production server outage.",
        sender="ops@company.com"
    )

    print("Classification Result:")
    print(f"  Category: {result['category']}")
    print(f"  Priority: {result['priority']}")
    print(f"  Urgency Score: {result['urgency_score']}")
    print(f"  Sentiment: {result['sentiment']}")
    print(f"  Requires Action: {result['requires_action']}")
    print(f"  Reasoning: {result['reasoning']}")


# Example 2: Apply Custom User Rules
async def example_custom_rules():
    """Apply user-defined priority rules"""

    user_preferences = {
        'whitelist_senders': ['boss@company.com', 'ceo@company.com'],
        'blacklist_senders': ['newsletter@marketing.com', 'promotions@ads.com'],
        'priority_rules': [
            {
                'sender_pattern': r'.*@vip-client\.com',
                'priority': 'urgent',
                'category': 'work'
            },
            {
                'subject_contains': 'invoice',
                'priority': 'high',
                'category': 'finance'
            }
        ]
    }

    # Initial AI classification
    ai_classification = {
        'category': 'other',
        'priority': 'medium',
        'urgency_score': 0.5,
        'sentiment': 'neutral',
        'requires_action': False,
        'reasoning': 'Standard email'
    }

    # Apply custom rules
    priority_engine = PriorityEngine(user_preferences)
    final_classification = priority_engine.apply_custom_rules(
        email={
            'subject': 'Invoice #12345',
            'sender_email': 'billing@vendor.com',
            'body': 'Please find attached your invoice for this month.'
        },
        ai_classification=ai_classification
    )

    print("\nCustom Rules Applied:")
    print(f"  Original Priority: {ai_classification['priority']}")
    print(f"  Final Priority: {final_classification['priority']}")
    print(f"  Final Category: {final_classification['category']}")


# Example 3: Generate Embeddings and Find Similar Emails
async def example_semantic_search():
    """Generate embeddings and find similar emails"""

    embedding_service = EmbeddingService()
    db = SessionLocal()

    try:
        # Get an email from database
        email = db.query(Email).first()

        if email:
            # Generate embedding
            embedding = embedding_service.embed_email(email)
            print(f"\nGenerated embedding with {len(embedding)} dimensions")

            # Update email with embedding
            email.embedding = embedding
            db.commit()

            # Find similar emails
            similar_emails = embedding_service.find_similar_emails(str(email.id), limit=5)

            print(f"\nFound {len(similar_emails)} similar emails:")
            for similar in similar_emails:
                print(f"  - {similar.subject[:50]}...")

    finally:
        db.close()


# Example 4: Calculate Confidence Score
async def example_confidence_calculation():
    """Calculate confidence score for classification"""

    confidence_service = ConfidenceService()

    ai_classification = {
        'category': 'work',
        'priority': 'high',
        'urgency_score': 0.8,
        'sentiment': 'neutral',
        'requires_action': True,
        'reasoning': 'Work-related urgent request'
    }

    # Scenario 1: User rules applied, with matching similar emails
    confidence = confidence_service.calculate_confidence(
        ai_classification=ai_classification,
        user_rules_applied=True,
        similar_emails=[
            type('Email', (), {'category': 'work'}),
            type('Email', (), {'category': 'work'}),
            type('Email', (), {'category': 'personal'})
        ]
    )

    requires_review = confidence_service.should_require_review(confidence)

    print("\nConfidence Calculation:")
    print(f"  Confidence Score: {confidence:.2f}")
    print(f"  Requires Review: {requires_review}")

    # Scenario 2: No user rules, no similar emails
    confidence_low = confidence_service.calculate_confidence(
        ai_classification=ai_classification,
        user_rules_applied=False,
        similar_emails=[]
    )

    requires_review_low = confidence_service.should_require_review(confidence_low)

    print(f"\n  Low Confidence Score: {confidence_low:.2f}")
    print(f"  Requires Review: {requires_review_low}")


# Example 5: Complete Triage Pipeline
async def example_complete_triage():
    """Run the complete triage pipeline"""

    complete_triage = CompleteTriageService()
    db = SessionLocal()

    try:
        # Create a sample email (or fetch from database)
        email = Email(
            subject="Meeting Request: Q4 Planning",
            body_text="I'd like to schedule a meeting to discuss Q4 planning. Are you available next Tuesday?",
            sender_email="manager@company.com",
            sender_name="John Manager"
        )

        # User preferences
        user_preferences = {
            'whitelist_senders': ['manager@company.com'],
            'blacklist_senders': [],
            'priority_rules': [
                {
                    'subject_contains': 'meeting',
                    'priority': 'high',
                    'category': 'work'
                }
            ]
        }

        # Process email through complete pipeline
        result = await complete_triage.process_email(email, user_preferences)

        print("\nComplete Triage Result:")
        print(f"  Category: {result['classification']['category']}")
        print(f"  Priority: {result['classification']['priority']}")
        print(f"  Urgency Score: {result['classification']['urgency_score']}")
        print(f"  Sentiment: {result['classification']['sentiment']}")
        print(f"  Requires Action: {result['classification']['requires_action']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Requires Review: {result['requires_review']}")
        print(f"  Similar Emails Found: {len(result['similar_emails'])}")
        print(f"  Reasoning: {result['classification']['reasoning']}")

    finally:
        db.close()


# Example 6: Batch Processing Multiple Emails
async def example_batch_processing():
    """Process multiple emails in batch"""

    complete_triage = CompleteTriageService()
    db = SessionLocal()

    try:
        # Fetch unprocessed emails
        emails = db.query(Email).filter(
            Email.processed_at.is_(None)
        ).limit(10).all()

        user_preferences = {
            'whitelist_senders': ['boss@company.com'],
            'blacklist_senders': ['spam@example.com'],
            'priority_rules': []
        }

        print(f"\nProcessing {len(emails)} emails...")

        results = []
        for email in emails:
            result = await complete_triage.process_email(email, user_preferences)
            results.append(result)

            print(f"  ✓ Processed: {email.subject[:40]}... -> {result['classification']['priority']}")

        # Summary statistics
        high_priority = sum(1 for r in results if r['classification']['priority'] in ['high', 'urgent'])
        needs_review = sum(1 for r in results if r['requires_review'])

        print(f"\nBatch Summary:")
        print(f"  Total Processed: {len(results)}")
        print(f"  High/Urgent Priority: {high_priority}")
        print(f"  Needs Review: {needs_review}")

    finally:
        db.close()


# Example 7: Error Handling
async def example_error_handling():
    """Demonstrate error handling"""

    complete_triage = CompleteTriageService()

    # Email with missing fields
    email = Email(
        subject=None,
        body_text=None,
        sender_email=None
    )

    result = await complete_triage.process_email(email, {})

    print("\nError Handling Example:")
    print(f"  Classification: {result['classification']['category']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Requires Review: {result['requires_review']}")
    print(f"  Reasoning: {result['classification']['reasoning']}")


# Run all examples
async def main():
    """Run all examples"""
    print("=" * 60)
    print("AI Triage Engine Examples")
    print("=" * 60)

    await example_basic_classification()
    await example_custom_rules()
    # await example_semantic_search()  # Requires database with emails
    await example_confidence_calculation()
    # await example_complete_triage()  # Requires OpenAI API key
    # await example_batch_processing()  # Requires database with emails
    await example_error_handling()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Note: Ensure you have set OPENAI_API_KEY in your .env file
    # and have a running PostgreSQL database with pgvector extension
    asyncio.run(main())
