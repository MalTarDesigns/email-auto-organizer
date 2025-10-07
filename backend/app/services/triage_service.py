from openai import OpenAI
import json
from app.core.config import settings


class TriageService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
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

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
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
        except Exception as e:
            # Return default classification on error
            return {
                'category': 'other',
                'priority': 'medium',
                'urgency_score': 0.5,
                'sentiment': 'neutral',
                'requires_action': False,
                'reasoning': f'Classification failed: {str(e)}'
            }

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for semantic search"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            # Return empty embedding on error
            return [0.0] * 1536
