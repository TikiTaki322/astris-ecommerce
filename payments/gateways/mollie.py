import os
import logging
import requests

from django.urls import reverse

from payments.gateways.base import PaymentGateway
from payments.types import PaymentSession

from shared.utils import get_current_domain
from core.models import Order

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


CURRENT_DOMAIN = get_current_domain()
REDIRECT_URL = CURRENT_DOMAIN if CURRENT_DOMAIN != 'localhost:8000' else os.getenv('NGROK_DOMAIN')

MOLLIE_API_KEY = os.getenv('MOLLIE_API_KEY')
MOLLIE_BASE_URL = 'https://api.mollie.com/v2/payments'

MOLLIE_STATUS_TO_INTERNAL = {
    'open': 'initiated',
    'pending': 'initiated',
    'authorized': 'initiated',
    'paid': 'succeeded',
    'failed': 'failed',
    'canceled': 'failed',
    'expired': 'failed',
}


class MollieGateway(PaymentGateway):
    def create_payment_session(self, order: Order, currency: str, user_id: int) -> PaymentSession | None:
        redirect_url = f'http://{CURRENT_DOMAIN}{reverse("payments:success")}'
        webhook_url = f'https://{REDIRECT_URL}{reverse("payments:mollie_webhook")}'  # /payments/api/v1/mollie/webhook/

        headers = {
            'Authorization': f'Bearer {MOLLIE_API_KEY}',
            'Content-Type': 'application/json',
        }
        payload = {
            'amount': {
                'currency': currency,
                'value': str(order.amount)
            },
            'description': f'Order-{order.id}',
            'redirectUrl': redirect_url,
            'webhookUrl': webhook_url,
            'method': 'twint',
            'metadata': {
                'user_id': str(user_id),
                'order_id': str(order.id),
                'items': [
                    {'name': item.product.name, 'quantity': item.quantity, 'price': str(item.price)}
                    for item in order.items.select_related('product')
                ]
            },
        }

        try:
            response = requests.post(MOLLIE_BASE_URL, json=payload, headers=headers, timeout=5)
            if response.status_code != 201:
                logger.error(
                    f"[ERROR] Error during payment session creation | Unexpected status code: {response.status_code} | "
                    f"Response: {response.text}")
                return None

            payment_session = response.json()
            session_id = payment_session.get('id')
            checkout_url = payment_session.get('_links', {}).get('checkout', {}).get('href')
            if not session_id or not checkout_url:
                logger.error(f'[ERROR] Missing session ID or checkout URL from Mollie response')
                return None

            logger.warning(f'[OK] Payment session was created successfully | Transaction ID: "{session_id}" | '
                           f'Subtotal: {payment_session.get("amount")} | Customer: {order.user} | '
                           f'Order items: {payment_session.get("metadata", {}).get("items")}\n')
            return PaymentSession(session_id=session_id, checkout_url=checkout_url)

        except requests.RequestException as e:
            logger.error(f'[ERROR] Network/API error during payment creation: {e}')
            return None
        except ValueError:
            logger.error(f'[ERROR] Invalid JSON from response when payment creation')
            return None

    def handle_webhook(self, mollie_webhook_data: dict) -> str:
        transaction_id = mollie_webhook_data.get('id')
        try:
            headers = {'Authorization': f'Bearer {MOLLIE_API_KEY}'}
            response = requests.get(f'{MOLLIE_BASE_URL}/{transaction_id}', headers=headers, timeout=5)
            if response.status_code != 200:
                logger.error(f'[ERROR] Error while webhook handling | Unexpected status code: {response.status_code} | '
                             f'Response: {response.text} | Transaction ID: "{transaction_id}"')
                return 'failed'

            payment_session = response.json()
            mollie_status = payment_session.get('status')
            if mollie_status not in MOLLIE_STATUS_TO_INTERNAL:
                logger.warning(f'[WARNING] Unmapped Mollie status: {mollie_status}')
            internal_status = MOLLIE_STATUS_TO_INTERNAL.get(mollie_status, 'failed')
            return internal_status

        except requests.RequestException as e:
            logger.error(f'[ERROR] Network/API error during webhook processing: {e}')
            return 'failed'
        except ValueError:
            logger.error(f'[ERROR] Invalid JSON from response when webhook processing')
            return 'failed'

    def check_payment_status(self, transaction_id: str) -> str:
        return NotImplementedError

        # print('🔄 Status was updated')
        # В реальных кейсах webhook может не дойти (сетевой сбой, блокировка, баг). В таких случаях ты:
        #   не обновишь статус и не покажешь пользователю результат.
        # Поэтому:
        #   check_payment_status(session_id) полезен для ручной проверки в административной части.
        # Также его можно:
        #   вызывать через Celery с отложкой (если статус "initiated" дольше 5 мин),
        #   использовать в fallback-механизме (см. стратегию webhook + poll backup).
