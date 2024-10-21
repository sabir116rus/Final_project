# orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from .cart import Cart
from django.views.decorators.http import require_POST
from .models import OrderItem
from django.contrib.auth.decorators import login_required
from .forms import OrderCreateForm
from django.contrib import messages
from datetime import datetime, time

@login_required
def order_create(request):
    cart = Cart(request)
    if not cart:
        messages.error(request, 'Ваша корзина пуста.')
        return redirect('product_list')

    current_time = datetime.now().time()
    if not time(9, 0) <= current_time <= time(18, 0):
        messages.error(request, 'Извините, заказы принимаются только с 9:00 до 18:00.')
        return redirect('cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = cart.get_total_price()
            order.save()
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            # Очистить корзину
            cart.clear()
            messages.success(request, f'Ваш заказ №{order.id} успешно оформлен!')
            return render(request, 'orders/order_created.html', {'order': order})
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    if not product.available:
        messages.error(request, 'Извините, этот товар недоступен для заказа.')
        return redirect('product_list')
    cart.add(product=product)
    messages.success(request, f'Товар "{product.name}" добавлен в корзину.')
    return redirect('product_list')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f'Товар "{product.name}" удален из корзины.')
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'orders/cart_detail.html', {'cart': cart})
