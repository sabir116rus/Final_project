# telegram_bot/handlers.py

from aiogram import types
from .bot import dp
from django.conf import settings
from orders.models import Order

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.answer("Здравствуйте! Это бот для уведомлений о заказах.")


@dp.message_handler(commands=['orders'])
async def list_orders(message: types.Message):
    if str(message.from_user.id) != settings.ADMIN_TELEGRAM_ID:
        await message.answer("У вас нет доступа к этой информации.")
        return

    # Импортируем здесь, чтобы избежать проблем с импортами
    from orders.models import Order

    orders = Order.objects.filter(status='pending')
    if orders.exists():
        response = "Текущие заказы:\n"
        for order in orders:
            response += f"Заказ №{order.id}, пользователь: {order.user.username}, сумма: {order.total_price} руб.\n"
    else:
        response = "Нет новых заказов."
    await message.answer(response)

@dp.message_handler(lambda message: str(message.from_user.id) == settings.ADMIN_TELEGRAM_ID, commands=['set_status'])
async def set_order_status(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("Используйте формат команды: /set_status <order_id> <status>")
            return
        order_id = int(parts[1])
        status = parts[2]
        if status not in dict(Order.STATUS_CHOICES).keys():
            await message.answer("Некорректный статус заказа.")
            return
        order = Order.objects.get(id=order_id)
        order.status = status
        order.save()
        await message.answer(f"Статус заказа №{order_id} изменен на '{order.get_status_display()}'.")
    except Order.DoesNotExist:
        await message.answer("Заказ с указанным ID не найден.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
