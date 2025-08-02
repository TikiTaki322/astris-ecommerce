from django.conf import settings


def log_webhook_source(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if settings.DEBUG:
            print(f"Webhook hit from IP: {request.META.get('REMOTE_ADDR')}, UA: {request.META.get('HTTP_USER_AGENT')}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view