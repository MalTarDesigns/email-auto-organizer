from typing import Dict, List
import re


class PriorityEngine:
    def __init__(self, user_preferences: dict):
        self.preferences = user_preferences
        self.priority_keywords = {
            'urgent': ['urgent', 'asap', 'immediate', 'critical', 'emergency'],
            'high': ['important', 'priority', 'deadline', 'today'],
            'medium': ['please review', 'feedback', 'update'],
            'low': ['fyi', 'newsletter', 'notification']
        }

    def apply_custom_rules(self, email: dict, ai_classification: dict) -> dict:
        """Apply user-defined rules to override or adjust AI classification"""

        # Check whitelist/blacklist
        if email['sender_email'] in self.preferences.get('whitelist_senders', []):
            ai_classification['priority'] = 'high'

        if email['sender_email'] in self.preferences.get('blacklist_senders', []):
            ai_classification['priority'] = 'low'

        # Apply custom priority rules
        custom_rules = self.preferences.get('priority_rules', [])
        for rule in custom_rules:
            if self._matches_rule(email, rule):
                ai_classification['priority'] = rule['priority']
                ai_classification['category'] = rule.get('category', ai_classification['category'])

        # Keyword-based priority boost
        subject_lower = email['subject'].lower()
        for priority, keywords in self.priority_keywords.items():
            if any(kw in subject_lower for kw in keywords):
                if self._priority_level(priority) > self._priority_level(ai_classification['priority']):
                    ai_classification['priority'] = priority

        return ai_classification

    def _matches_rule(self, email: dict, rule: dict) -> bool:
        """Check if email matches custom rule conditions"""
        try:
            if 'sender_pattern' in rule:
                if not re.search(rule['sender_pattern'], email['sender_email']):
                    return False

            if 'subject_contains' in rule:
                if rule['subject_contains'].lower() not in email['subject'].lower():
                    return False

            return True
        except Exception as e:
            # If pattern matching fails, rule doesn't match
            return False

    def _priority_level(self, priority: str) -> int:
        """Convert priority to numeric level for comparison"""
        levels = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        return levels.get(priority, 2)
