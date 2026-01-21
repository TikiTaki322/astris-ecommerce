import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.backends.cache import SessionStore
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_verification_token():
    return uuid.uuid4().hex


def get_user_by_verification_token(token):
    from django.apps import apps
    UserProfile = apps.get_model('accounts', 'UserProfile')
    return UserProfile.objects.filter(verification_token=token).first()


def link_lifetime_check(email_sent_at):
    expiration_time = email_sent_at + timedelta(minutes=10)
    return expiration_time > timezone.now()


def invalidate_all_user_sessions(user):
    if settings.SESSION_ENGINE == 'django.contrib.sessions.backends.db':
        # using ORM
        user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in user_sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(user.pk):
                session.delete()
                logger.info(f'Deleted DB session for user {user.email}')

    elif settings.SESSION_ENGINE == 'django.contrib.sessions.backends.cache':
        # scanning Redis
        redis_client = cache.client.get_client()
        cursor = 0

        while True:
            cursor, keys = redis_client.scan(cursor, match='*django.contrib.sessions.cache*', count=100)
            for key in keys:
                try:
                    full_key = key.decode()
                    session_key = full_key.split('django.contrib.sessions.cache')[-1]
                    session = SessionStore(session_key=session_key)

                    if session.get('_auth_user_id') == str(user.pk):
                        session.flush()
                        logger.info(f'Deleted Redis session for user {user.email}')

                except Exception as e:
                    logger.error(f'Error invalidating session {session_key}: {e}')
                    continue

            if cursor == 0:
                break