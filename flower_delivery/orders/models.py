# orders/models.py

import asyncio
from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from telegram_bot.bot import bot

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),           # Новый заказ
        ('accepted', 'Принят к работе'),     # Принят к работе
        ('in_progress', 'Находится в работе'), # В процессе выполнения
        ('in_delivery', 'В доставке'),       # В доставке
        ('completed', 'Выполнен'),           # Завершен
        ('canceled', 'Отменен'),             # Отменен
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)

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

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена на момент заказа

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def get_cost(self):
        return self.price * self.quantity



# Асинхронная функция для отправки уведомления о новом заказе
async def send_telegram_notification(order):
    await bot.send_message(
        settings.ADMIN_TELEGRAM_ID,
        f"Новый заказ №{order.id} от пользователя {order.user.username}. Сумма: {order.total_price} руб."
    )

# Сигнал, который срабатывает при создании нового заказа
@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    if created:
        try:
            # Создаем новый цикл событий
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_telegram_notification(instance))
            loop.close()
        except Exception as e:
            print(f"Ошибка при отправке уведомления в Telegram: {e}")