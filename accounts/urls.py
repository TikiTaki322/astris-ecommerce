from django.urls import path
from django.views.generic import TemplateView

from .views.auth import UserLoginView, UserLogoutView
from .views.email_change import UserEmailChangeView, UserEmailChangeConfirmView
from .views.password_change import UserPasswordChangeView, UserNewPasswordSetupView, UserPasswordResetView
from .views.profile import BackofficeDashboardView, CustomerAccountView, UserLoginLogsListView, ShippingInfoGenericView
from .views.register import UserRegisterView, UserRegisterConfirmView

app_name = 'accounts'

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('confirm-register/', UserRegisterConfirmView.as_view(), name='confirm_register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),

    path('dashboard/', BackofficeDashboardView.as_view(), name='backoffice_dashboard'),
    path('account/', CustomerAccountView.as_view(), name='customer_account'),
    path('account/shipping/', ShippingInfoGenericView.as_view(), name='shipping_info'),
    path('account/login-history/', UserLoginLogsListView.as_view(), name='login_logs'),
    path('account/password-reset/', UserPasswordResetView.as_view(), name='password_reset'),
    path('account/password-change/', UserPasswordChangeView.as_view(), name='password_change'),
    path('account/new-password-setup/', UserNewPasswordSetupView.as_view(), name='new_password_setup'),
    path('account/email-change/', UserEmailChangeView.as_view(), name='email_change'),
    path('account/confirm-email-change/', UserEmailChangeConfirmView.as_view(), name='confirm_email_change'),

    path('email-sent/', TemplateView.as_view(template_name='accounts/email_sent.html'), name='email_sent'),
]