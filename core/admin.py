from django.contrib import admin

from core.models import Product, ProductImage, Category, Order, OrderItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # quantity of empty forms by default


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'price', 'quantity', 'is_active')
    inlines = [ProductImageInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'user', 'shipping_email', 'status', 'items_amount', 'delivery_amount', 'total_amount',
        'paid_at', 'shipped_at', 'notified_at', 'delivered_at'
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(status__in=('pending', 'expired'))


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'product_quantity', 'product_unit_price', 'product_total_price')


admin.site.register(Category)