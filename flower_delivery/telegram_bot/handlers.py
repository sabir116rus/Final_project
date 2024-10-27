# telegram_bot/handlers.py

from aiogram import Router, types
from aiogram.filters import Command
from django.conf import settings
from orders.models import Order
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from datetime import datetime
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay

def register_handlers():
    router = Router()

    @router.message(Command(commands=['start', 'help']))
    async def send_welcome(message: types.Message):
        await message.answer(
            "Здравствуйте! Это бот для уведомлений о заказах.\n\n"
            "Доступные команды:\n"
            "/orders - список новых заказов\n"
            "/orders_status - список заказов со статусами\n"
            "/set_status <order_id> <status> - установить статус заказа\n"
            "/daily_report - отчет по продажам за сегодня\n"
            "/link <username> - связать ваш Telegram с аккаунтом на сайте"
        )

    @router.message(Command(commands=['orders']))
    async def list_orders(message: types.Message):
        if str(message.from_user.id) != settings.ADMIN_TELEGRAM_ID:
            await message.answer("У вас нет доступа к этой информации.")
            return

        orders = await sync_to_async(list)(
            Order.objects.filter(status='pending').values('id', 'user__username', 'total_price')
        )

        if orders:
            response = "Текущие заказы в статусе 'В ожидании':\n"
            for order in orders:
                response += (
                    f"Заказ №{order['id']}, пользователь: {order['user__username']}, "
                    f"сумма: {order['total_price']} руб.\n"
                )
        else:
            response = "Нет новых заказов."
        await message.answer(response)

    @router.message(Command(commands=['orders_status']))
    async def list_orders_with_status(message: types.Message):
        if str(message.from_user.id) != settings.ADMIN_TELEGRAM_ID:
            await message.answer("У вас нет доступа к этой информации.")
            return

        orders = await sync_to_async(list)(
            Order.objects.all()
            .order_by('status', '-created_at')
            .values('id', 'user__username', 'total_price', 'status')
        )

        if orders:
            status_display = dict(Order.STATUS_CHOICES)
            response = "Список всех заказов:\n"
            for order in orders:
                status = status_display.get(order['status'], 'Неизвестно')
                response += (
                    f"Заказ №{order['id']}, пользователь: {order['user__username']}, "
                    f"сумма: {order['total_price']} руб., статус: {status}\n"
                )
        else:
            response = "Нет заказов."
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

            order = await sync_to_async(Order.objects.get)(id=order_id)
            order.status = status
            await sync_to_async(order.save)()
            await message.answer(
                f"Статус заказа №{order_id} изменен на '{order.get_status_display()}'."
            )
        except Order.DoesNotExist:
            await message.answer("Заказ с указанным ID не найден.")
        except Exception as e:
            await message.answer(f"Произошла ошибка: {e}")

    @router.message(Command(commands=['daily_report']))
    async def daily_report(message: types.Message):
        if str(message.from_user.id) != settings.ADMIN_TELEGRAM_ID:
            await message.answer("У вас нет доступа к этой информации.")
            return

        today = datetime.now().date()
        orders_today = await sync_to_async(Order.objects.filter)(created_at__date=today)

        total_orders = await sync_to_async(orders_today.count)()
        total_revenue = await sync_to_async(
            lambda: orders_today.aggregate(total=Sum('total_price'))['total'] or 0
        )()

        response = f"Отчет по продажам за {today.strftime('%d.%m.%Y')}:\n"
        response += f"Всего заказов: {total_orders}\n"
        response += f"Общая выручка: {total_revenue} руб.\n"

        await message.answer(response)

    @router.message(Command(commands=['link']))
    async def link_account(message: types.Message):
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Пожалуйста, отправьте команду в формате: /link your_username")
            return
        username = args[1]
        try:
            user = await sync_to_async(User.objects.get)(username=username)
            profile = user.profile
            profile.telegram_id = str(message.from_user.id)
            await sync_to_async(profile.save)()
            await message.answer(
                f"Ваш аккаунт связан с пользователем {username}. "
                f"Вы будете получать уведомления о статусе заказов."
            )
        except User.DoesNotExist:
            await message.answer("Пользователь с таким именем не найден.")

    return router
