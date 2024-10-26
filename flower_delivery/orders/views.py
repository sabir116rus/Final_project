# orders/views.py

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
from asgiref.sync import async_to_sync, sync_to_async
from aiogram import Bot
import os
from aiogram.types import FSInputFile
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay

@login_required
def order_create(request):
    cart = Cart(request)
    if not cart:
        messages.error(request, 'Ваша корзина пуста.')
        return redirect('product_list')

    current_time = datetime.now().time()
    if not time(1, 0) <= current_time <= time(23, 0):
        messages.error(request, 'Извините, заказы принимаются только с 1:00 до 23:00.')
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

            # Передаем order в send_order_notification
            async_to_sync(send_order_notification)(order)

            return render(request, 'orders/order_created.html', {'order': order})
    else:
        form = OrderCreateForm()
    return render(request, 'orders/order_create.html', {'cart': cart, 'form': form})


# Асинхронная функция для отправки уведомления
async def send_order_notification(order):
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        # Получаем необходимые данные из ORM в синхронном контексте
        def get_order_data():
            first_item = order.items.first()
            product_image_path = first_item.product.image.path if first_item else None
            text = (
                f"🛍 <b>Новый заказ №{order.id}</b>\n"
                f"👤 Пользователь: {order.user.username}\n"
                f"💰 Сумма: {order.total_price} руб.\n"
                f"📅 Дата и время заказа: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"📍 Адрес доставки: {order.address}\n"
                f"📞 Телефон: {order.phone}\n"
                f"📝 Комментарий: {order.comment or 'Нет'}"
            )
            return product_image_path, text

        product_image_path, text = await sync_to_async(get_order_data)()

        if product_image_path and os.path.exists(product_image_path):
            photo = FSInputFile(product_image_path)
            await bot.send_photo(
                chat_id=settings.ADMIN_TELEGRAM_ID,
                photo=photo,
                caption=text,
                parse_mode='HTML'
            )
        else:
            await bot.send_message(
                chat_id=settings.ADMIN_TELEGRAM_ID,
                text=text,
                parse_mode='HTML'
            )
        await bot.session.close()  # Закрываем сессию бота
    except Exception as e:
        print(f"Ошибка при отправке уведомления в Telegram: {e}")

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    if not product.available:
        messages.error(request, 'Извините, этот товар недоступен для заказа.')
        return redirect('product_list')
    quantity = request.POST.get('quantity', 1)
    try:
        quantity = int(quantity)
    except ValueError:
        quantity = 1
    cart.add(product=product, quantity=quantity)
    messages.success(request, f'Товар "{product.name}" добавлен в корзину.')
    return redirect('product_list')

@require_POST
def cart_update(request):
    cart = Cart(request)
    for item in cart:
        product_id = str(item['product'].id)
        quantity = request.POST.get('quantity_' + product_id)
        if quantity:
            try:
                quantity = int(quantity)
                if quantity > 0:
                    cart.add(product=item['product'], quantity=quantity, override_quantity=True)
                else:
                    cart.remove(item['product'])
            except ValueError:
                messages.error(request, f'Введите корректное количество для товара {item["product"].name}')
    messages.success(request, 'Корзина успешно обновлена.')
    return redirect('cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f'Товар "{product.name}" удален из корзины.')
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'orders/cart_detail.html', {'cart': cart})

@staff_member_required
def sales_report(request):
    # Агрегируем данные по дням
    sales_data = Order.objects.values(date=TruncDay('created_at')).annotate(
        total_orders=Count('id'),
        total_revenue=Sum('total_price')
    ).order_by('-date')

    return render(request, 'orders/sales_report.html', {'sales_data': sales_data})