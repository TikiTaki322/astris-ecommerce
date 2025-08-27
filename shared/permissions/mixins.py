from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse

from .utils import is_authenticated, is_staff_or_seller


class StaffOrSellerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_staff_or_seller(self.request)

    def handle_no_permission(self):
        if not self.test_func():
            return redirect(reverse('shared:permission_denied'))


class AuthRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_authenticated(self.request)

    def handle_no_permission(self):
        if not self.test_func():
            return redirect(f"{reverse('accounts:login')}?info=login_required")
