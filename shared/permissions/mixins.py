from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse

from .utils import is_authenticated, is_backoffice_member


class BackofficeAccessRequiredMixin(UserPassesTestMixin):
    """
    Access for any user with elevated privileges: staff/seller/manager/etc
    """
    def test_func(self):
        return is_backoffice_member(self.request)

    def handle_no_permission(self):
        if not self.test_func():
            return redirect(reverse('shared:permission_denied'))


class AuthRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_authenticated(self.request)

    def handle_no_permission(self):
        if not self.test_func():
            return redirect(f"{reverse('accounts:login')}?info=login_required")
