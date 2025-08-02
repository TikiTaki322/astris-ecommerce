from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .models import UserProfile, CustomerProfile, SellerProfile


admin.site.register(CustomerProfile)
admin.site.register(SellerProfile)


@admin.register(UserProfile)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additionally', {'fields': ('phone', 'role')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'email_verified')