from openai import OpenAI
from sqlalchemy import func
from app.models.email import Email
from app.core.database import SessionLocal
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000]  # Limit text length
            )
            return response.data[0].embedding
        except Exception as e:
            # Return empty embedding on error
            return [0.0] * 1536

    def embed_email(self, email: Email) -> list[float]:
        """Generate embedding for email content"""
        # Combine subject and body for embedding
        content = f"{email.subject} {email.body_text[:1000] if email.body_text else ''}"
        return self.generate_embedding(content)

    def find_similar_emails(self, email_id: str, limit: int = 5) -> list:
        """Find similar emails using vector similarity"""
        db = SessionLocal()

        try:
            # Get target email
            target_email = db.query(Email).filter(Email.id == email_id).first()

            if not target_email or target_email.embedding is None:
                return []

            # Find similar emails using cosine distance
            # pgvector uses <=> operator for cosine distance in raw SQL
            # In SQLAlchemy, we use the l2_distance function and filter for non-null embeddings
            similar_emails = db.query(Email).filter(
                Email.id != email_id,
                Email.embedding.isnot(None)
            ).order_by(
                Email.embedding.cosine_distance(target_email.embedding)
            ).limit(limit).all()

            return similar_emails

        except Exception as e:
            # Return empty list on error
            return []
        finally:
            db.close()
