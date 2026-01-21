from django.urls import path
from django.views.generic import TemplateView

from payments.views import ReviewOrderView, start_payment, mollie_webhook, start_checkout

app_name = 'payments'

urlpatterns = [
    path('start-checkout/', start_checkout, name='start_checkout'),
    path('review-order/', ReviewOrderView.as_view(), name='review_order'),
    path('start-payment/<int:pk>/', start_payment, name='start_payment'),
    path('api/v1/mollie/webhook/', mollie_webhook, name='mollie_webhook'),
    path('payment-initiated/', TemplateView.as_view(template_name='payments/payment_initiated.html'), name='payment_initiated'),
    path('something-went-wrong/', TemplateView.as_view(template_name='payments/generic_error.html'), name='something_went_wrong'),
]