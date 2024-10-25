# orders/models.py

from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from django.conf import settings
from asgiref.sync import async_to_sync, sync_to_async
from aiogram import Bot

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),  # Новый заказ
        ('accepted', 'Принят к работе'),  # Принят к работе
        ('in_progress', 'Находится в работе'),  # В процессе выполнения
        ('in_delivery', 'В доставке'),  # В доставке
        ('completed', 'Выполнен'),  # Завершен
        ('canceled', 'Отменен'),  # Отменен
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий к заказу')

    def status_color(self):
        status_colors = {
            'pending': 'warning',
            'accepted': 'info',
            'in_progress': 'primary',
            'in_delivery': 'secondary',
            'completed': 'success',
            'canceled': 'danger',
        }
        return status_colors.get(self.status, 'light')

    status_color.short_description = 'Цвет статуса'

    def __str__(self):
        return f'Заказ №{self.id} от {self.user.username}'

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def save(self, *args, **kwargs):
        previous_status = None
        if self.pk:
            previous_status = Order.objects.get(pk=self.pk).status
        super().save(*args, **kwargs)
        if previous_status and previous_status != self.status:
            # Статус изменился, отправляем уведомление
            async_to_sync(send_status_change_notification)(self)


# Асинхронная функция для отправки уведомления об изменении статуса
async def send_status_change_notification(order):
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        # Получаем необходимые данные из ORM в синхронном контексте
        def get_notification_data():
            text = (
                f"🔔 <b>Статус вашего заказа №{order.id} изменен</b>\n"
                f"Новый статус: <b>{order.get_status_display()}</b>"
            )
            telegram_id = order.user.profile.telegram_id
            return text, telegram_id

        text, telegram_id = await sync_to_async(get_notification_data)()

        # Отправляем уведомление администратору
        await bot.send_message(
            chat_id=settings.ADMIN_TELEGRAM_ID,
            text=text,
            parse_mode='HTML'
        )
        # Если пользователь связал свой аккаунт с Telegram, отправляем ему уведомление
        if telegram_id:
            await bot.send_message(
                chat_id=telegram_id,
                text=text,
                parse_mode='HTML'
            )
        await bot.session.close()  # Закрываем сессию бота
    except Exception as e:
        print(f"Ошибка при отправке уведомления в Telegram: {e}")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена на момент заказа

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def get_cost(self):
        return self.price * self.quantity
