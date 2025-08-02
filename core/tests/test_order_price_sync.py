import unittest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from accounts.signals import create_specific_profile, create_shop_for_seller
from accounts.models import CustomerProfile, SellerProfile
from core.models import Shop, Product, Order, OrderItem
from core.services.order_price_sync import OrderPriceSyncService

User = get_user_model()


# Ты тестишь логику внутри сервиса, которая зависит от моделей, но не от всей системы
# Ты строишь модели как foundation, не тестируешь их поведение
# Это -> Service layer test или Unit-of-Work test (юнит логической работы)


class OrderPriceSyncServiceTestCase(TestCase):
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
        self.order = Order.objects.create(user=self.customer_profile)
        self.order_item_1 = OrderItem.objects.create(
            order=self.order,
            product=self.product_1,
            quantity=6,
            unit_price=self.product_1.price,
            price=Decimal(self.product_1.price * 6)
        )
        self.order_item_2 = OrderItem.objects.create(
            order=self.order,
            product=self.product_2,
            quantity=3,
            unit_price=self.product_2.price,
            price=Decimal(self.product_2.price * 3)
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

    def test_compute_order_amount(self):
        service = OrderPriceSyncService(order=self.order)
        amount = service.get_amount()

        order_items = [item.price for item in service.order.items.all()]
        expected_amount = sum(order_items)
        self.assertEqual(amount, expected_amount)  # Decimal('100.62')

    def test_compute_session_amount(self):
        service = OrderPriceSyncService(session_order=self.session_order)
        amount = service.get_amount()

        session_items = [Decimal(item['price']) for item in service.session_order.values()]
        expected_amount = sum(session_items)
        self.assertEqual(amount, expected_amount)  # Decimal('100.62')

    def test_sync_order_items_with_price_changes(self):
        new_product_price = Decimal('7.18')
        self.product_1.price = new_product_price
        self.product_1.save()

        service = OrderPriceSyncService(order=self.order)
        price_diff = service.sync()
        self.assertTrue(price_diff)

        self.order_item_1.refresh_from_db()
        self.assertEqual(self.order_item_1.unit_price, new_product_price)

    def test_sync_session_items_with_price_changes(self):
        new_product_price = Decimal('2.83')
        self.product_2.price = new_product_price
        self.product_2.save()

        service = OrderPriceSyncService(session_order=self.session_order)
        price_diff = service.sync()
        self.assertTrue(price_diff)

        cart_item = service.session_order[str(self.product_2.pk)]
        self.assertEqual(cart_item['unit_price'], str(new_product_price))

    def test_sync_generic_items_no_price_changes(self):
        service = OrderPriceSyncService(order=self.order)
        price_diff = service.sync()
        self.assertFalse(price_diff)

        service = OrderPriceSyncService(session_order=self.session_order)
        price_diff = service.sync()
        self.assertFalse(price_diff)

    def test_compute_empty_amount(self):
        """ Defensive testcase cuz logic in views prevent existence an empty order/session """
        order = Order.objects.create(user=self.customer_profile)  # An empty order
        service = OrderPriceSyncService(order=order)
        self.assertEqual(service.get_amount(), Decimal('0.00'))

        service = OrderPriceSyncService(order=None)
        self.assertEqual(service.get_amount(), Decimal('0.00'))

        service = OrderPriceSyncService(session_order={})
        self.assertEqual(service.get_amount(), Decimal('0.00'))
