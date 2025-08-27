from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import SellerProfile, CustomerProfile, UserLoginHistory


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_specific_profile(sender, instance, created, **kwargs):
    if created and instance.role.lower() == 'customer' and instance.email_verified is True:
        CustomerProfile.objects.create(user=instance)
    if instance.role.lower() == 'seller' and not hasattr(instance, 'seller_profile'):
        SellerProfile.objects.create(user=instance)
        if hasattr(instance, 'customer_profile'):
            (profile := CustomerProfile.objects.filter(user=instance).first()) and profile.hard_delete()


@receiver(post_save, sender=SellerProfile)
def create_shop_for_seller(sender, instance, created, **kwargs):
    if created:
        from django.apps import apps
        Shop = apps.get_model('core', 'Shop')
        name = f'Shop_{instance.user.username}' if instance.user.username else 'Default Shop'
        Shop.objects.create(owner=instance, name=name)


@receiver(user_logged_in)
def create_login_record(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR', '')
    ua = request.META.get('HTTP_USER_AGENT', '')
    UserLoginHistory.objects.create(user=user, email=user.email, ip_address=ip, user_agent=ua)