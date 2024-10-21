# products/views.py

from django.shortcuts import render
from .models import Product

def product_list(request):
    products = Product.objects.all()
# Получаем все продукты из базы данных
    return render(request, 'products/product_list.html', {'products': products})