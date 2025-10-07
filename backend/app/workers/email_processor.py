from celery import Task
from app.celery_app import celery_app
from app.models.email import Email
from app.core.database import SessionLocal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, max_retries=3)
def process_email(self, email_id: str):
    """
    Background task to process and classify email

    Args:
        email_id: UUID of the email to process

    Returns:
        Dict with processing status
    """
    db = SessionLocal()

    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logger.error(f"Email not found: {email_id}")
            return {'error': 'Email not found', 'email_id': email_id}

        # NOTE: TriageService will be implemented in Phase 3
        # For now, we'll mark the email as processed without classification

        # Placeholder for future triage service integration:
        # triage_service = TriageService()
        # classification = triage_service.classify_email(
        #     subject=email.subject,
        #     body=email.body_text,
        #     sender=email.sender_email
        # )
        #
        # email.category = classification['category']
        # email.priority = classification['priority']
        # email.urgency_score = classification['urgency_score']
        # email.sentiment = classification['sentiment']
        # email.requires_action = classification['requires_action']

        # For now, just mark as processed
        email.processed_at = datetime.utcnow()

        db.commit()

        logger.info(f"Email processed successfully: {email_id}")
        return {
            'status': 'processed',
            'email_id': email_id,
            'note': 'Email marked as processed. Classification will be added in Phase 3.'
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing email {email_id}: {str(e)}")

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    finally:
        db.close()


@celery_app.task(base=DatabaseTask, bind=True, max_retries=3)
def batch_process_emails(self, email_ids: list):
    """
    Process multiple emails in batch

    Args:
        email_ids: List of email UUIDs to process

    Returns:
        Dict with batch processing results
    """
    results = {
        'total': len(email_ids),
        'successful': 0,
        'failed': 0,
        'errors': []
    }

    for email_id in email_ids:
        try:
            result = process_email.delay(str(email_id))
            results['successful'] += 1
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'email_id': str(email_id),
                'error': str(e)
            })
            logger.error(f"Failed to queue email {email_id}: {str(e)}")

    return results
