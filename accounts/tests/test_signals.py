from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import CustomerProfile
from core.models import Shop

User = get_user_model()


class SignalsTestCase(TestCase):
    def setUp(self):
        self.common_user = User.objects.create_user(
            email='common_user@mail.ru',
            email_verified=True,
            password='StrongPas123'
        )

    def test_customer_profile_created_for_verified_user(self):
        self.assertIsNotNone(CustomerProfile.objects.filter(user=self.common_user).first())

    def test_seller_profile_created_via_admin_panel(self):
        """ Simulation of creating a seller manually through the admin, without email_verified """
        self.panel_seller = User.objects.create_user(
            email='panel_seller@mail.ru',
            password='StrongPas123',
            role=User.Role.SELLER
        )
        self.assertIsNone(CustomerProfile.objects.filter(user=self.panel_seller).first())
        self.assertIsNotNone(SellerProfile.objects.filter(user=self.panel_seller).first())
        self.assertIsNotNone(Shop.objects.filter(owner=self.panel_seller.seller_profile).first())

    def test_seller_profile_created_and_customer_profile_removed_on_role_change(self):
        self.common_user.role = User.Role.SELLER
        self.common_user.save()

        self.assertIsNone(CustomerProfile.objects.filter(user=self.common_user).first())
        self.assertIsNotNone(SellerProfile.objects.filter(user=self.common_user).first())
        self.assertIsNotNone(Shop.objects.filter(owner=self.common_user.seller_profile).first())
