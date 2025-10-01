from django.db import models
from django.utils.functional import cached_property

from shared.models import TimeStampedModel
from accounts.models import SellerProfile, CustomerProfile

from decimal import Decimal


class Shop(TimeStampedModel):
    owner = models.OneToOneField(SellerProfile, on_delete=models.CASCADE, related_name='shop')
    name = models.CharField(max_length=56)

    def __str__(self):
        return f'{self.name}'


class Category(TimeStampedModel):
    name = models.CharField(max_length=56, unique=True)
    description = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f'{self.name}'


class Product(TimeStampedModel):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=56, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    quantity = models.PositiveIntegerField(default=1)
    description = models.CharField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)

    def get_primary_image(self):
        return self.images.filter(is_primary=True).first()

    def get_secondary_image(self):
        return self.images.exclude(is_primary=True).order_by('position', 'created_at').first()

    def has_image(self):
        return self.images.exists()

    def __str__(self):
        return f'{self.name}'


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=1)
    alt_text = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ['position']

    def save(self, *args, **kwargs):
        if not self.pk and not self.product.has_image():
            self.is_primary = True
        elif self.is_primary:
            self.product.images.exclude(pk=self.pk).update(is_primary=False)
            self.position = 1
        else:
            self.position = self.get_next_element() if self.position == 1 else self.position

        super().save(*args, **kwargs)

    def get_next_element(self):
        return self.product.images.count() + 1

    def get_image_url(self):
        return self.image.url

    def get_alt_text(self):
        return self.alt_text


class Order(TimeStampedModel):
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        SHIPPED = 'shipped', 'Shipped'
        CANCELLED = 'cancelled', 'Cancelled'
        DELIVERED = 'delivered', 'Delivered'

    user = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    tracking_info = models.CharField(max_length=128, blank=True, null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    price_diff = models.BooleanField(default=False)

    paid_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    notified_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    shipping_email = models.EmailField(max_length=40, blank=True, null=True)
    shipping_first_name = models.CharField(max_length=56)
    shipping_last_name = models.CharField(max_length=56)
    shipping_phone = models.CharField(max_length=24)
    shipping_country = models.CharField(max_length=56)
    shipping_city = models.CharField(max_length=56)
    shipping_postal_code = models.CharField(max_length=16)
    shipping_street = models.CharField(max_length=56)
    shipping_house_number = models.CharField(max_length=16)
    shipping_apartment = models.CharField(max_length=16, blank=True, null=True)
    shipping_additional_info = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f'Order #{self.pk}'

    @cached_property
    def latest_payment(self):
        return self.payments.order_by('-created_at').first()

    @property
    def payment_method(self):
        return self.latest_payment.payment_method if self.latest_payment else None

    @property
    def payment_status(self):
        return self.latest_payment.payment_status if self.latest_payment else None

    @property
    def delivery_price(self):
        return Decimal('8.50') if self.amount < 50 else Decimal('0.00')


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id_snapshot = models.PositiveIntegerField()
    product_name = models.CharField(max_length=56)
    product_quantity = models.PositiveIntegerField(default=1)
    product_description = models.CharField(max_length=256, blank=True)
    product_unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    product_total_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f'{self.product_name}'


class Payment(TimeStampedModel):
    class PaymentMethod(models.TextChoices):
        CARD = 'card', 'Card'
        TWINT = 'twint', 'Twint'
        PAYPAL = 'paypal', 'Paypal'
        CRYPTO = 'crypto', 'Crypto'

    class PaymentStatus(models.TextChoices):
        INITIATED = 'initiated', 'Initiated'
        SUCCEEDED = 'succeeded', 'Succeeded'
        FAILED = 'failed', 'Failed'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices)
    transaction = models.CharField(max_length=128, blank=True, null=True)  # Outer payment provider
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'Payment #{self.pk} by {self.order.user}'
