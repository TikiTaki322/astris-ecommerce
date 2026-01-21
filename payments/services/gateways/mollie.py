import logging
from typing import Literal

import requests
from django.conf import settings
from django.urls import reverse

from payments.services.gateways import PaymentGateway
from payments.types import PaymentSession
from shared.utils import get_current_domain

logger = logging.getLogger(__name__)

CURRENT_DOMAIN = get_current_domain()
REDIRECT_URL = CURRENT_DOMAIN if CURRENT_DOMAIN != 'localhost:8000' else settings.NGROK_DOMAIN

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
    def create_payment_session(self, order, user_id: int, payment_method: str,
                               currency: Literal['CHF'] = 'CHF') -> PaymentSession | None:
        redirect_url = f'http://{CURRENT_DOMAIN}{reverse("payments:payment_initiated")}'
        webhook_url = f'https://{REDIRECT_URL}{reverse("payments:mollie_webhook")}'  # /payments/api/v1/mollie/webhook/

        headers = {
            'Authorization': f'Bearer {settings.MOLLIE_API_KEY}',
            'Content-Type': 'application/json',
        }
        payload = {
            'amount': {
                'currency': currency,
                'value': str(order.total_amount)
            },
            'description': f'Order-{order.pk}',
            'redirectUrl': redirect_url,
            'webhookUrl': webhook_url,
            'method': payment_method,
            'metadata': {
                'user_id': str(user_id),
                'order_id': str(order.pk),
                'items': [
                    {
                        'name': item.product_name,
                        'quantity': item.product_quantity,
                        'price': str(item.product_total_price),
                    }
                    for item in order.items.all()
                ]
            },
        }

        try:
            response = requests.post(settings.MOLLIE_BASE_URL, json=payload, headers=headers, timeout=5)
            if response.status_code != 201:
                logger.error(
                    f"Error during payment session creation | Unexpected status code: {response.status_code} | "
                    f"Response: {response.text}")
                logger.error(f'{payload=}')
                return None

            payment_session = response.json()
            session_id = payment_session.get('id', None)
            checkout_url = payment_session.get('_links', {}).get('checkout', {}).get('href', None)
            if not session_id or not checkout_url:
                logger.error(f'Missing session ID or checkout URL from Mollie response')
                return None

            logger.info(f'Payment session was created successfully | Transaction ID: "{session_id}" | '
                        f'Subtotal: {payment_session.get("amount")} | Customer: {order.user} | '
                        f'Order items: {payment_session.get("metadata", {}).get("items")}')
            return PaymentSession(session_id=session_id, checkout_url=checkout_url)

        except requests.RequestException as e:
            logger.error(f'Network/API error during payment creation: {e}')
            return None
        except ValueError:
            logger.error(f'Invalid JSON from response during payment creation')
            return None

    def handle_webhook(self, mollie_webhook_data: dict) -> str:
        transaction_id = mollie_webhook_data.get('id', None)
        try:
            headers = {'Authorization': f'Bearer {settings.MOLLIE_API_KEY}'}
            response = requests.get(f'{settings.MOLLIE_BASE_URL}/{transaction_id}', headers=headers, timeout=5)
            if response.status_code != 200:
                logger.error(f'Error while webhook handling | Unexpected status code: {response.status_code} | '
                             f'Response: {response.text} | Transaction ID: "{transaction_id}"')
                return 'failed'

            payment_session = response.json()
            mollie_status = payment_session.get('status', None)
            if mollie_status not in MOLLIE_STATUS_TO_INTERNAL:
                logger.warning(f'Unmapped Mollie status: {mollie_status}')
            internal_status = MOLLIE_STATUS_TO_INTERNAL.get(mollie_status, 'failed')
            return internal_status

        except requests.RequestException as e:
            logger.error(f'Network/API error during webhook processing: {e}')
            return 'failed'
        except ValueError:
            logger.error(f'Invalid JSON from response when webhook processing')
            return 'failed'

    def check_payment_status(self, transaction_id: str) -> str:
        return NotImplemented

        # В реальных кейсах webhook может не дойти (сетевой сбой, блокировка, баг).
        # В таких случаях статус не обновится
        # Поэтому:
        #   check_payment_status(session_id) полезен для ручной проверки в административной части.
        # Также его можно:
        #   вызывать через Celery с отложкой (если статус "initiated" дольше 5 мин),
        #   использовать в fallback-механизме (стратегия webhook + poll backup).

        # UPD: я не знаю как это тестить, потому никак не реализовал, на практике, когда я руками тестил транзакции,
        # я ловил желтый Джанго-экран, но после фикса ошибок и перезапуска страницы браузера, вебхук бил в эндпоинт
        # и заказ переводился в статус оплачено, не зависимо от первоначального краша.
