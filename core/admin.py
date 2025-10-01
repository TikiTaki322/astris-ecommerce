from django.contrib import admin
from .models import Product, ProductImage, Shop, Category, Order, OrderItem, Payment


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1  # quantity of empty forms by default


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]


admin.site.register(Shop)
admin.site.register(Category)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
