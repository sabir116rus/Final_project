# users/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),  # Добавлено next_page
    path('profile/', views.profile, name='profile'),
    path('profile/cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('profile/order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('profile/reorder/<int:order_id>/', views.reorder, name='reorder'),
]
