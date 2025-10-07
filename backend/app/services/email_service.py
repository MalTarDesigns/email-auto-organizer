from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
from email.utils import parsedate_to_datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, user_credentials: dict):
        """
        Initialize email service with user credentials

        Args:
            user_credentials: Dict containing token, refresh_token, client_id, client_secret
        """
        self.credentials = Credentials(
            token=user_credentials.get('token'),
            refresh_token=user_credentials.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=user_credentials.get('client_id'),
            client_secret=user_credentials.get('client_secret')
        )
        self.service = build('gmail', 'v1', credentials=self.credentials)

    def fetch_emails(self, max_results: int = 50, page_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch recent emails from Gmail

        Args:
            max_results: Maximum number of emails to fetch
            page_token: Token for pagination

        Returns:
            Dict with emails list and next page token
        """
        try:
            # Build request parameters
            request_params = {
                'userId': 'me',
                'maxResults': max_results,
                'labelIds': ['INBOX']
            }

            if page_token:
                request_params['pageToken'] = page_token

            results = self.service.users().messages().list(**request_params).execute()

            messages = results.get('messages', [])
            emails = []

            for msg in messages:
                try:
                    email_data = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    parsed_email = self._parse_email(email_data)
                    if parsed_email:
                        emails.append(parsed_email)
                except HttpError as e:
                    logger.error(f"Error fetching email {msg['id']}: {str(e)}")
                    continue

            return {
                'emails': emails,
                'next_page_token': results.get('nextPageToken')
            }

        except HttpError as e:
            logger.error(f"Error fetching emails: {str(e)}")
            raise Exception(f"Error fetching emails: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Error fetching emails: {str(e)}")

    def _parse_email(self, email_data: dict) -> Optional[Dict[str, Any]]:
        """
        Parse Gmail API response into structured format

        Args:
            email_data: Raw email data from Gmail API

        Returns:
            Parsed email dict or None if parsing fails
        """
        try:
            headers = {h['name']: h['value']
                      for h in email_data['payload']['headers']}

            # Extract body
            body_text = ""
            body_html = ""

            if 'parts' in email_data['payload']:
                body_text, body_html = self._extract_body_from_parts(email_data['payload']['parts'])
            else:
                # Single part message
                if 'body' in email_data['payload'] and 'data' in email_data['payload']['body']:
                    mime_type = email_data['payload'].get('mimeType', '')
                    decoded_body = base64.urlsafe_b64decode(
                        email_data['payload']['body']['data']
                    ).decode('utf-8', errors='ignore')

                    if 'text/html' in mime_type:
                        body_html = decoded_body
                    else:
                        body_text = decoded_body

            # Parse sender
            sender_email, sender_name = self._parse_sender(headers.get('From', ''))

            # Parse date
            received_at = self._parse_date(headers.get('Date', ''))

            return {
                'message_id': email_data['id'],
                'subject': headers.get('Subject', ''),
                'sender_email': sender_email,
                'sender_name': sender_name,
                'received_at': received_at,
                'body_text': body_text or email_data.get('snippet', ''),
                'body_html': body_html,
                'snippet': email_data.get('snippet', '')
            }

        except Exception as e:
            logger.error(f"Error parsing email: {str(e)}")
            return None

    def _extract_body_from_parts(self, parts: List[dict]) -> tuple[str, str]:
        """
        Extract text and HTML body from email parts

        Args:
            parts: List of email parts

        Returns:
            Tuple of (body_text, body_html)
        """
        body_text = ""
        body_html = ""

        for part in parts:
            mime_type = part.get('mimeType', '')

            # Handle nested parts (multipart)
            if 'parts' in part:
                nested_text, nested_html = self._extract_body_from_parts(part['parts'])
                body_text = body_text or nested_text
                body_html = body_html or nested_html
                continue

            # Extract body data
            if 'body' in part and 'data' in part['body']:
                try:
                    decoded_body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8', errors='ignore')

                    if mime_type == 'text/plain' and not body_text:
                        body_text = decoded_body
                    elif mime_type == 'text/html' and not body_html:
                        body_html = decoded_body

                except Exception as e:
                    logger.warning(f"Failed to decode part: {str(e)}")
                    continue

        return body_text, body_html

    def _parse_sender(self, from_header: str) -> tuple[str, str]:
        """
        Parse sender email and name from From header

        Args:
            from_header: From header value

        Returns:
            Tuple of (email, name)
        """
        try:
            # Format: "Name <email@example.com>" or "email@example.com"
            if '<' in from_header and '>' in from_header:
                name = from_header.split('<')[0].strip().strip('"')
                email = from_header.split('<')[1].split('>')[0].strip()
                return email, name
            else:
                return from_header.strip(), ""
        except Exception:
            return from_header, ""

    def _parse_date(self, date_header: str) -> Optional[datetime]:
        """
        Parse date from email header

        Args:
            date_header: Date header value

        Returns:
            datetime object or None
        """
        try:
            return parsedate_to_datetime(date_header)
        except Exception:
            return None

    def refresh_credentials(self) -> Credentials:
        """
        Refresh OAuth credentials

        Returns:
            Refreshed credentials
        """
        try:
            from google.auth.transport.requests import Request
            self.credentials.refresh(Request())
            return self.credentials
        except Exception as e:
            logger.error(f"Error refreshing credentials: {str(e)}")
            raise Exception(f"Failed to refresh credentials: {str(e)}")
