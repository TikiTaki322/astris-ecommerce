# import unittest
# from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from accounts.signals import create_specific_profile, create_shop_for_seller
from accounts.models import CustomerProfile, SellerProfile
from core.models import Shop, Product, Order, OrderItem
from core.services.order_builder import OrderBuilderService

User = get_user_model()


class OrderBuilderServiceTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(create_specific_profile, sender=settings.AUTH_USER_MODEL)
        post_save.disconnect(create_shop_for_seller, sender=SellerProfile)

    @classmethod
    def tearDownClass(cls):
        post_save.connect(create_specific_profile, sender=settings.AUTH_USER_MODEL)
        post_save.connect(create_shop_for_seller, sender=SellerProfile)
        super().tearDownClass()

    def setUp(self):
        self.seller_user = User.objects.create_user(
            username='test_seller',
            email='seller@mail.ru',
            email_verified=True,
            password='StrongPas123',
            role=User.Role.SELLER
        )
        self.seller_profile = SellerProfile.objects.create(user=self.seller_user)

        self.customer_user = User.objects.create_user(
            username='test_customer',
            email='customer@mail.ru',
            email_verified=True,
            password='StrongPas123'
        )
        self.customer_profile = CustomerProfile.objects.create(user=self.customer_user)

        self.shop = Shop.objects.create(owner=self.seller_profile, name='Test Shop')
        self.product_1 = Product.objects.create(
            shop=self.shop,
            name='Test Product 1',
            price=Decimal('9.33'),
            quantity=10
        )
        self.product_2 = Product.objects.create(
            shop=self.shop,
            name='Test Product 2',
            price=Decimal('14.88'),
            quantity=10
        )

        self.session_order = {
            str(self.product_1.pk): {
                'product_pk': self.product_1.pk,
                'product_name': self.product_1.name,
                'quantity': 6,
                'unit_price': str(self.product_1.price),
                'price': str(Decimal(self.product_1.price * 6))
            },
            str(self.product_2.pk): {
                'product_pk': self.product_2.pk,
                'product_name': self.product_2.name,
                'quantity': 3,
                'unit_price': str(self.product_2.price),
                'price': str(Decimal(self.product_2.price * 3))
            }
        }

    def test_creates_order_items_from_session(self):
        service = OrderBuilderService(session_order=self.session_order, user=self.customer_user)
        order = service.build()

        self.assertEqual(order.items.count(), 2)
        item_1 = order.items.get(product=self.product_1)
        item_2 = order.items.get(product=self.product_2)
        self.assertEqual(item_1.quantity, 6)
        self.assertEqual(item_2.quantity, 3)

    def test_updates_order_items_from_session(self):
        order = Order.objects.create(user=self.customer_profile)
        OrderItem.objects.create(order=order, product=self.product_1, quantity=2,
                                 unit_price=self.product_1.price, price=self.product_1.price * 2)

        service = OrderBuilderService(session_order=self.session_order, user=self.customer_user)
        updated_order = service.build()

        item = updated_order.items.get(product=self.product_1)
        self.assertEqual(item.quantity, 8)  # 2 (old from initial order) + 6 (new from session)

    def test_sets_price_diff_when_inconsistency_detected(self):
        order = Order.objects.create(user=self.customer_profile)
        mock_price = Decimal('3.33')
        OrderItem.objects.create(order=order, product=self.product_1, quantity=4,
                                 unit_price=mock_price, price=mock_price * 4)

        self.product_1.price = Decimal('1.12')
        self.product_1.save()

        service = OrderBuilderService(session_order=self.session_order, user=self.customer_user)
        order = service.build()
        item = order.items.get(product=self.product_1)
        self.assertTrue(order.price_diff)
        self.assertEqual(item.quantity, 10)  # 4 (old from initial order) + 6 (new from session)

    def test_returns_none_when_session_empty(self):
        """ Defensive testcase cuz logic in views prevent order_builder from triggering on an empty session """
        service = OrderBuilderService(session_order={}, user=self.customer_user)
        order = service.build()
        self.assertIsNone(order)
