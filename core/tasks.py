import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.sessions.backends.cache import SessionStore
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from core.models import Order
from core.services.stock_reservation import StockReservationService

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_pending_orders():
    cutoff = timezone.now() - timedelta(hours=24)
    order_pks = []

    expired_orders = Order.objects.filter(
        status=OrderStatus.PENDING,
        updated_at__lt=cutoff
    ).prefetch_related('items')

    for order in expired_orders:
        for order_item in order.items.all():
            StockReservationService(cart_item=order_item).release_reserved_stock()

        order_pks.append(order.pk)
        logger.info(f'Cleared expired order #{order.pk} for user {order.user.user.email}')

    if order_pks:
        Order.objects.filter(pk__in=order_pks).update(
            status=OrderStatus.EXPIRED,
            expired_at=timezone.now()
        )
        logger.info(f'Order cleanup: removed {len(order_pks)} expired orders')


@shared_task
def cleanup_expired_session_orders():
    redis_client = cache.client.get_client()
    cutoff = timezone.now() - timedelta(hours=23)
    cursor = 0
    cleaned_count = 0

    # iteratively scanning Redis
    while True:
        # getting ~100 keys at a time (doesn't block Redis)
        cursor, keys = redis_client.scan(cursor, match='*django.contrib.sessions.cache*', count=100)

        for key in keys:
            try:
                full_key = key.decode()
                session_key = full_key.split('django.contrib.sessions.cache')[-1]  # Django stores as "prefix:version:session_key"
                session = SessionStore(session_key=session_key)

                session_order = session.get('session_order')
                if not session_order:
                    continue

                last_modified = parse_datetime(session_order.get('modified_at'))  # str to datetime
                if last_modified < cutoff:
                    for session_item in session_order['items'].values():
                        StockReservationService(cart_item=session_item).release_reserved_stock()

                    del session['session_order']
                    session.save()
                    cleaned_count += 1

            except Exception as e:
                logger.warning(f'Error cleaning session {session_key}: {e}')
                continue

        if cursor == 0:
            break

    if cleaned_count > 0:
        logger.info(f'Session cleanup: removed {cleaned_count} expired carts')