import logging

from celery import shared_task
from django.template.loader import render_to_string

from core.models import Order
from .services.email_sender import send_email_via_resend

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_email_task(self, email_type: str, to_emails: list | str, context: dict):
    """ Generic task with typing for monitoring """
    EMAIL_TEMPLATES = {
        'registration': {
            'subject': 'Register account on Astris',
            'html': 'emails/registration_request.html',
            'txt': 'emails/registration_request.txt',
            'max_retries': 3
        },
        'password_change': {
            'subject': 'Change password on Astris',
            'html': 'emails/password_change_request.html',
            'txt': 'emails/password_change_request.txt',
            'max_retries': 3
        },
        'password_reset': {
            'subject': 'Reset password on Astris',
            'html': 'emails/password_reset_request.html',
            'txt': 'emails/password_reset_request.txt',
            'max_retries': 3
        },
        'email_change': {
            'subject': 'Change email on Astris',
            'html': 'emails/email_change_request.html',
            'txt': 'emails/email_change_request.txt',
            'max_retries': 3
        },
        'order_shipped': {
            'subject': 'Your order is on its way!',
            'html': 'emails/order_shipped_notification.html',
            'txt': 'emails/order_shipped_notification.txt',
            'max_retries': 10
        },
    }

    try:
        config = EMAIL_TEMPLATES[email_type]
        if email_type == 'order_shipped':
            order = Order.objects.prefetch_related('items').get(pk=context.get('order_pk', None))
            context = {'order': order}

        html_content = render_to_string(config['html'], context)
        text_content = render_to_string(config['txt'], context)

        logger.info(f"Email's been initiated | type={email_type} | to={to_emails}")

        send_email_via_resend(
            to_emails=to_emails,
            subject=config['subject'],
            html_content=html_content,
            text_content=text_content,
        )

    except Exception as exc:
        if self.request.retries < config["max_retries"]:
            logger.warning(
                f'Email retry {self.request.retries + 1}/{config["max_retries"]} | '
                f'type={email_type} | error={exc}'
            )
            raise self.retry(exc=exc, countdown=60, max_retries=config["max_retries"])
        else:
            logger.error(
                f'Email task failed after {config["max_retries"]} retries | '
                f'type={email_type} | to={to_emails} | error={exc}'
            )
            raise