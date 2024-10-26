# orders/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('order/create/', views.order_create, name='order_create'),
    path('sales_report/', views.sales_report, name='sales_report'),
]
