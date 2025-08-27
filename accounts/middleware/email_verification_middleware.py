from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404

from django.conf import settings

from shared.permissions.utils import is_authenticated

import logging

logger = logging.getLogger(__name__)


class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # For static routes
        self.exempt_urls = [
            reverse('accounts:confirm_register'),
            reverse('accounts:email_sent'),
            reverse('accounts:login'),
            reverse('core:product_list'),
            reverse('core:orderitem_list'),
            reverse('shared:delete_session_keys'),
        ]

        # For dynamic routes (with parameters as pk/slug)
        self.exempt_view_names = [
            'product_detail',
            'orderitem_create',
            # 'orderitem_update',
            'orderitem_delete',
        ]

        self.exempt_prefixes = []
        if settings.DEBUG:
            self.exempt_prefixes += ['/static/', '/media/', '/favicon.ico']

    def __call__(self, request):
        static_path = request.path
        # logger.info(f'🙏🏻 Start of middleware pipline: {static_path=}')
        try:
            # Handle dynamic routes via resolve
            dynamic_path = resolve(request.path_info).url_name
        except Resolver404:
            logger.info(f'❌ Resolver404 invoked with attempt to resolve {request.path_info}')
            return self.get_response(request)

        is_static_or_media = any(static_path.startswith(prefix) for prefix in self.exempt_prefixes)

        if not is_authenticated(request) and request.session.get('pending_user'):
            if not ((static_path in self.exempt_urls) or (dynamic_path in self.exempt_view_names) or is_static_or_media):
                logger.info(f'❌ Access blocked: {static_path=} | {dynamic_path=} | {is_static_or_media}')
                return redirect(reverse('accounts:email_sent'))
            logger.info(f'✅ Access allowed: {static_path=} | {dynamic_path=} | {is_static_or_media}')
        return self.get_response(request)
