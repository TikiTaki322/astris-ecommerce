from dotenv import load_dotenv

import requests
import logging
import os

load_dotenv()
logger = logging.getLogger(__name__)


RESEND_API_URL = 'https://api.resend.com/emails'
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
FROM_EMAIL = "Rawpapers <noreply@rawpapers.store>"

if not RESEND_API_KEY:
    raise EnvironmentError('No RESEND_API_KEY found in environment variables')


def send_email_via_resend(to_emails: list | str, subject, html_content, text_content=None):
    if isinstance(to_emails, str):
        to_emails = [to_emails]

    payload = {
        'from': FROM_EMAIL,
        'to': to_emails,
        'subject': subject,
        'html': html_content,
    }
    if text_content:
        payload['text'] = text_content

    headers = {
        'Authorization': f'Bearer {RESEND_API_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        RESEND_API_URL,
        json=payload,
        headers=headers
    )

    # logger.warning(f"HEADERS: {response.headers}")
    logger.warning(f"SENDING TO: {', '.join(to_emails)}")
    logger.warning(f"BODY: {response.text}")

    if response.status_code not in (202, 200):
        raise Exception(f'STATUS: {response.status_code}')

    logger.warning(f'Email successfully sent | STATUS: {response.status_code}')
    return response
