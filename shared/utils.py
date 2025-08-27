from django.shortcuts import redirect
from django.utils import timezone
from django.conf import settings
from django.urls import reverse


from urllib.parse import urlencode


def redirect_with_message(view_name, filters=None, **params):
    if filters:
        params.update(filters)
    url = f'{reverse(view_name)}?{urlencode(params)}'
    return redirect(url)


def get_request_user(request):
    return getattr(request, 'user', None)


def is_authenticated_user(request):
    user = get_request_user(request)
    return bool(user and user.is_authenticated)


def is_staff_or_seller(request):
    if is_authenticated_user(request):
        user = get_request_user(request)
        return bool(user and (user.is_staff or user.role == 'seller'))


def is_order_owner(request, order):
    return bool(order.user.user == request.user)


def get_current_domain(request=None):
    if request:
        return request.get_host()
    return settings.BASE_DOMAIN if not settings.DEBUG else 'localhost:8000'


def extract_audit_data_from_request(request):
    return {
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'N/A'),
        'timestamp': timezone.now()
    }


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or 'N/A'