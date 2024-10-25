# telegram_bot/handlers.py

from aiogram import Router, types
from aiogram.filters import Command
from django.conf import settings
from orders.models import Order
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

def register_handlers():
    router = Router()

    @router.message(Command(commands=['start', 'help']))
    async def send_welcome(message: types.Message):
        await message.answer("Здравствуйте! Это бот для уведомлений о заказах.")

    @router.message(Command(commands=['orders']))
    async def list_orders(message: types.Message):
        if str(message.from_user.id) != settings.ADMIN_TELEGRAM_ID:
            await message.answer("У вас нет доступа к этой информации.")
            return

        # Оборачиваем вызовы Django ORM в sync_to_async
        # Используем values() для получения необходимых данных без связанных полей
        orders = await sync_to_async(list)(
            Order.objects.filter(status='pending').values('id', 'user__username', 'total_price')
        )

        if orders:
            response = "Текущие заказы:\n"
            for order in orders:
                response += f"Заказ №{order['id']}, пользователь: {order['user__username']}, сумма: {order['total_price']} руб.\n"
        else:
            response = "Нет новых заказов."
        await message.answer(response)

    @router.message(Command(commands=['set_status']))
    async def set_order_status(message: types.Message):
        if str(message.from_user.id) != settings.ADMIN_TELEGRAM_ID:
            await message.answer("У вас нет доступа к этой информации.")
            return

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

            # Оборачиваем вызовы Django ORM в sync_to_async
            order = await sync_to_async(Order.objects.get)(id=order_id)
            order.status = status
            await sync_to_async(order.save)()
            await message.answer(f"Статус заказа №{order_id} изменен на '{order.get_status_display()}'.")
        except Order.DoesNotExist:
            await message.answer("Заказ с указанным ID не найден.")
        except Exception as e:
            await message.answer(f"Произошла ошибка: {e}")

    @router.message(Command(commands=['link']))
    async def link_account(message: types.Message):
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Пожалуйста, отправьте команду в формате: /link your_username")
            return
        username = args[1]
        try:
            # Оборачиваем вызовы Django ORM в sync_to_async
            user = await sync_to_async(User.objects.get)(username=username)
            profile = user.profile
            profile.telegram_id = str(message.from_user.id)
            await sync_to_async(profile.save)()
            await message.answer(f"Ваш аккаунт связан с пользователем {username}. Вы будете получать уведомления о статусе заказов.")
        except User.DoesNotExist:
            await message.answer("Пользователь с таким именем не найден.")

    return router
