from celery import Task
from app.celery_app import celery_app
from app.services.email_service import EmailService
from app.models.email import Email
from app.models.user import User
from app.core.database import SessionLocal
from app.core.config import settings
from app.workers.email_processor import process_email
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
def fetch_new_emails(self, user_id: str):
    """
    Fetch new emails for a user

    Args:
        user_id: UUID of the user

    Returns:
        Dict with fetch results
    """
    db = SessionLocal()

    try:
        # Get user credentials
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.error(f"User not found: {user_id}")
            return {'error': 'User not found', 'user_id': user_id}

        # Check if token needs refresh
        if user.token_expires_at and user.token_expires_at <= datetime.utcnow():
            logger.info(f"Token expired for user {user_id}, attempting refresh")
            try:
                from app.api.v1.auth import refresh_token
                # Token will be refreshed automatically by EmailService
            except Exception as e:
                logger.error(f"Failed to refresh token: {str(e)}")
                return {
                    'error': 'Token refresh failed',
                    'user_id': user_id,
                    'details': str(e)
                }

        # Initialize email service
        email_service = EmailService({
            'token': user.access_token,
            'refresh_token': user.refresh_token,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET
        })

        # Fetch emails
        try:
            result = email_service.fetch_emails(max_results=50)
            emails_data = result['emails']
        except Exception as e:
            logger.error(f"Failed to fetch emails for user {user_id}: {str(e)}")

            # Retry with exponential backoff
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        # Store emails in database
        new_emails = 0
        processed_ids = []

        for email_data in emails_data:
            try:
                # Check if email already exists
                existing = db.query(Email).filter(
                    Email.message_id == email_data['message_id']
                ).first()

                if not existing:
                    email = Email(
                        user_id=user_id,
                        message_id=email_data['message_id'],
                        subject=email_data['subject'],
                        sender_email=email_data['sender_email'],
                        sender_name=email_data['sender_name'],
                        body_text=email_data['body_text'],
                        body_html=email_data.get('body_html'),
                        received_at=email_data['received_at']
                    )
                    db.add(email)
                    db.flush()  # Flush to get the ID
                    new_emails += 1

                    # Queue for processing
                    process_email.delay(str(email.id))
                    processed_ids.append(str(email.id))

            except Exception as e:
                logger.error(f"Error storing email {email_data.get('message_id')}: {str(e)}")
                continue

        db.commit()

        logger.info(f"Fetched {new_emails} new emails for user {user_id}")
        return {
            'status': 'success',
            'user_id': user_id,
            'new_emails': new_emails,
            'total_fetched': len(emails_data),
            'processed_ids': processed_ids
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error in fetch_new_emails for user {user_id}: {str(e)}")
        raise

    finally:
        db.close()


@celery_app.task(base=DatabaseTask, bind=True)
def sync_all_users_emails(self):
    """
    Periodic task to sync emails for all active users

    Returns:
        Dict with sync results for all users
    """
    db = SessionLocal()

    try:
        # Get all users
        users = db.query(User).all()

        results = {
            'total_users': len(users),
            'successful': 0,
            'failed': 0,
            'details': []
        }

        for user in users:
            try:
                # Queue email fetch for each user
                task = fetch_new_emails.delay(str(user.id))
                results['successful'] += 1
                results['details'].append({
                    'user_id': str(user.id),
                    'email': user.email,
                    'task_id': task.id,
                    'status': 'queued'
                })
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'user_id': str(user.id),
                    'email': user.email,
                    'status': 'failed',
                    'error': str(e)
                })
                logger.error(f"Failed to queue sync for user {user.id}: {str(e)}")

        logger.info(f"Sync queued for {results['successful']}/{results['total_users']} users")
        return results

    except Exception as e:
        logger.error(f"Error in sync_all_users_emails: {str(e)}")
        raise

    finally:
        db.close()


@celery_app.task(base=DatabaseTask, bind=True, max_retries=3)
def sync_user_emails_with_retry(self, user_id: str, max_results: int = 50):
    """
    Sync emails for a specific user with retry logic

    Args:
        user_id: UUID of the user
        max_results: Maximum number of emails to fetch

    Returns:
        Dict with sync results
    """
    try:
        return fetch_new_emails(user_id)
    except Exception as e:
        logger.error(f"Sync failed for user {user_id}: {str(e)}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes
