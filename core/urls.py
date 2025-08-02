from django.urls import path

from .views.order import OrderItemListView, OrderItemCreateView, OrderItemUpdateView, OrderItemDeleteView, \
    OrderListView, OrderDetailView
from .views.product import ProductListView, ProductGenericView, ProductDetailView, ProductDeleteView, \
    CategoryListView, CategoryGenericView, CategoryDeleteView


app_name = 'core'

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/create/', ProductGenericView.as_view(), name='product_create'),
    path('products/<int:pk>/update/', ProductGenericView.as_view(), name='product_update'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),

    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/create/', CategoryGenericView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', CategoryGenericView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),

    path('order-items/', OrderItemListView.as_view(), name='orderitem_list'),
    path('order-items/<int:pk>/create/', OrderItemCreateView.as_view(), name='orderitem_create'),
    # path('order-items/<int:pk>/update/', OrderItemUpdateView.as_view(), name='orderitem_update'),
    path('order-items/<int:pk>/delete/', OrderItemDeleteView.as_view(), name='orderitem_delete'),

    path('orders/', OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
]