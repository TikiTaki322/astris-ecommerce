from django.urls import path
from django.views.generic import TemplateView

from .views.password_change import UserPasswordChangeView, UserPasswordChangeConfirmView, UserPasswordResetView
from .views.profile import UserProfileView, UserLoginLogsListView, ShippingInfoGenericView, SellerDashboardView
from .views.email_update import UserEmailUpdateView, UserEmailUpdateConfirmView
from .views.register import UserRegisterView, UserRegisterConfirmView
from .views.auth import UserLoginView, UserLogoutView


app_name = 'accounts'

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('confirm-register/', UserRegisterConfirmView.as_view(), name='confirm_register'),

    path('profile/', UserProfileView.as_view(), name='profile'),
    path('seller-dashboard/', SellerDashboardView.as_view(), name='seller_dashboard'),
    path('profile/login-history/', UserLoginLogsListView.as_view(), name='login_logs'),

    path('profile/password-reset/', UserPasswordResetView.as_view(), name='password_reset'),
    path('profile/password-change/', UserPasswordChangeView.as_view(), name='password_change'),
    path('profile/confirm-password-change/', UserPasswordChangeConfirmView.as_view(), name='confirm_password_change'),
    path('profile/email-update/', UserEmailUpdateView.as_view(), name='email_update'),
    path('profile/confirm-email-update/', UserEmailUpdateConfirmView.as_view(), name='confirm_email_update'),

    path('shipping/', ShippingInfoGenericView.as_view(), name='shipping_info'),

    path('email-sent/', TemplateView.as_view(template_name='accounts/email_sent.html'), name='email_sent'),
]