import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email_via_resend(to_emails: list | str, subject: str, html_content: str, text_content: str = None):
    if isinstance(to_emails, str):
        to_emails = [to_emails]

    payload = {
        'from': settings.FROM_EMAIL,
        'to': to_emails,
        'subject': subject,
        'html': html_content,
    }
    if text_content:
        payload['text'] = text_content

    headers = {
        'Authorization': f'Bearer {settings.RESEND_API_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        settings.RESEND_API_URL,
        json=payload,
        headers=headers,
        timeout=10
    )

    # logger.info(f"HEADERS: {response.headers}")
    # logger.info(f"BODY: {response.text}")

    if response.status_code not in (202, 200):
        logger.error(f'Email delivery failed | status={response.status_code} | body={response.text}')
        raise Exception(f'Email delivery failed | status={response.status_code}')
    else:
        logger.info(f'Email sent successfully | to={", ".join(to_emails)} | status={response.status_code}')

    return response
