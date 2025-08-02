from django.contrib.sessions.models import Session
from django.utils import timezone

from datetime import timedelta
import uuid


def generate_email_verification_token():
    return uuid.uuid4().hex


def get_user_by_email_verification_token(token):
    from django.apps import apps
    UserProfile = apps.get_model('accounts', 'UserProfile')
    return UserProfile.objects.filter(email_verification_token=token).first()


def link_lifetime_check(email_sent_at):
    expiration_time = email_sent_at + timedelta(minutes=10)
    return expiration_time > timezone.now()


def invalidate_all_user_sessions(user):
    user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in user_sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id):
            session.delete()
            print(f'Session: {data} was deleted')
