from django.urls import path

from .views.category import CategoryListView, CategoryGenericView, CategoryDeleteView
from .views.delivery import DeliverySettingsDetailView, DeliverySettingsUpdateView
from .views.order import CartClearOutView, OrderListView, OrderChangeStatusView, OrderNotifyShippedView
from .views.order_item import OrderItemListView, OrderItemCreateView, OrderItemDeleteView
from .views.product import ProductListView, ProductGenericView, ProductDetailView, ProductDeleteView, \
    ProductToggleVisibilityView

app_name = 'core'

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/create/', ProductGenericView.as_view(), name='product_create'),
    path('products/<int:pk>/update/', ProductGenericView.as_view(), name='product_update'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('products/<int:pk>/toggle-visibility/', ProductToggleVisibilityView.as_view(), name='product_toggle_visibility'),

    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/create/', CategoryGenericView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', CategoryGenericView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),

    path('order-items/', OrderItemListView.as_view(), name='orderitem_list'),
    path('order-items/<int:pk>/create/', OrderItemCreateView.as_view(), name='orderitem_create'),
    # path('order-items/<int:pk>/update/', OrderItemUpdateView.as_view(), name='orderitem_update'),
    path('order-items/<int:pk>/delete/', OrderItemDeleteView.as_view(), name='orderitem_delete'),

    path('cart-clear-out/', CartClearOutView.as_view(), name='cart_clear_out'),

    path('orders/', OrderListView.as_view(), name='order_list'),

    path('orders/<int:pk>/change-status/', OrderChangeStatusView.as_view(), name='order_change_status'),
    path('orders/<int:pk>/mark-delivered/', OrderChangeStatusView.as_view(), name='order_delivered'),
    path('orders/<int:pk>/notify-shipped/', OrderNotifyShippedView.as_view(), name='order_notify_shipped'),

    path('delivery-settings/', DeliverySettingsDetailView.as_view(), name='delivery_settings_detail'),
    path('delivery-settings/update/', DeliverySettingsUpdateView.as_view(), name='delivery_settings_update'),
]