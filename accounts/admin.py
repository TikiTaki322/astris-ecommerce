from django.contrib import admin
from django.db.models import Count, Q

from accounts.models import UserProfile, CustomerProfile
from core.models import Order


@admin.register(UserProfile)
class CustomUserAdmin(admin.ModelAdmin):
    ordering = ('email',)
    search_fields = ('email',)
    list_display = ('email', 'role', 'email_verified', 'is_staff')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Additionally', {'fields': ('role', 'email_verified')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0
    fields = ('pk', 'status', 'items_amount', 'delivery_amount', 'total_amount', 'created_at')
    readonly_fields = ('pk', 'created_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(status__in=('pending', 'expired')).order_by('-created_at')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'orders_count')
    inlines = [OrderInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            orders_total=Count(
                'orders',
                filter=~Q(orders__status__in=['pending', 'expired'])
            )
        )
        return qs

    def orders_count(self, obj):
        return obj.orders_total