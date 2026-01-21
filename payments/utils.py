import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def log_webhook_source(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if settings.DEBUG:
            logger.info(f"Webhook hit from IP: {request.META.get('REMOTE_ADDR')}, UA: {request.META.get('HTTP_USER_AGENT')}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view