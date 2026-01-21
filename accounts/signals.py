from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import CustomerProfile, UserLoginHistory


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_specific_profile(sender, instance, **kwargs):
    """
    Invariant:
    - Customer must always have CustomerProfile
    - Backoffice members must not have CustomerProfile
    """
    if instance.role.lower() == 'customer':
        CustomerProfile.objects.get_or_create(user=instance)
    else:
        CustomerProfile.objects.filter(user=instance).delete()


@receiver(user_logged_in)
def create_login_record(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR', '')
    ua = request.META.get('HTTP_USER_AGENT', '')
    UserLoginHistory.objects.create(user=user, email=user.email, ip_address=ip, user_agent=ua)