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

        try:
            # Step 1: AI Classification
            ai_classification = self.triage_service.classify_email(
                subject=email.subject or '',
                body=email.body_text or '',
                sender=email.sender_email or ''
            )

            # Step 2: Apply user rules
            priority_engine = PriorityEngine(user_preferences)
            final_classification = priority_engine.apply_custom_rules(
                {
                    'subject': email.subject or '',
                    'sender_email': email.sender_email or '',
                    'body': email.body_text or ''
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
        except Exception as e:
            # Return default response on error
            return {
                'classification': {
                    'category': 'other',
                    'priority': 'medium',
                    'urgency_score': 0.5,
                    'sentiment': 'neutral',
                    'requires_action': False,
                    'reasoning': f'Processing failed: {str(e)}'
                },
                'confidence': 0.0,
                'requires_review': True,
                'similar_emails': []
            }
