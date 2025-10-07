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
