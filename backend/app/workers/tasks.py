from app.workers.celery_app import celery_app


@celery_app.task(name="process_email")
def process_email(email_id: str):
    """
    Process an email: classify, prioritize, and optionally generate response
    """
    # This will be implemented in Phase 3
    pass


@celery_app.task(name="sync_emails")
def sync_emails(user_id: str):
    """
    Sync emails from email provider for a specific user
    """
    # This will be implemented in Phase 2
    pass


@celery_app.task(name="generate_response")
def generate_response(email_id: str, tone: str = "professional"):
    """
    Generate AI response for an email
    """
    # This will be implemented in Phase 4
    pass
