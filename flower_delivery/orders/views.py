# orders/views.py

import asyncio
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from .cart import Cart
from django.views.decorators.http import require_POST
from .models import OrderItem, Order
from django.contrib.auth.decorators import login_required
from .forms import OrderCreateForm
from django.contrib import messages
from datetime import datetime, time
from django.conf import settings

# Импортируем бот
from telegram_bot.bot import bot

@login_required
def order_create(request):
    cart = Cart(request)
    if not cart:
        messages.error(request, 'Ваша корзина пуста.')
        return redirect('product_list')

    current_time = datetime.now().time()
    if not time(9, 0) <= current_time <= time(23, 0):
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

            # Передаем order и request в send_order_notification
            asyncio.run(send_order_notification(order, request))

            return render(request, 'orders/order_created.html', {'order': order})
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


# Асинхронная функция для отправки уведомления
async def send_order_notification(order, request):
    try:
        # Формируем сообщение
        text = (
            f"Новый заказ №{order.id}\n"
            f"Пользователь: {order.user.username}\n"
            f"Сумма: {order.total_price} руб.\n"
            f"Дата и время заказа: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Адрес доставки: {order.address}\n"
            f"Комментарий: {order.comment or 'Нет'}"
        )

        # Получаем первый товар из заказа для отправки изображения
        first_item = order.items.first()
        if first_item:
            product_image_url = request.build_absolute_uri(first_item.product.image.url)
            await bot.send_photo(
                chat_id=settings.ADMIN_TELEGRAM_ID,
                photo=product_image_url,
                caption=text
            )
        else:
            await bot.send_message(
                chat_id=settings.ADMIN_TELEGRAM_ID,
                text=text
            )
    except Exception as e:
        print(f"Ошибка при отправке уведомления в Telegram: {e}")

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