# products/models.py

from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    # Название продукта
    name = models.CharField(max_length=100, verbose_name='Название')
    # Цена продукта
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    # Изображение продукта
    image = models.ImageField(upload_to='products/', verbose_name='Изображение')
    available = models.BooleanField(default=True, verbose_name='В наличии')

    def __str__(self):
        return self.name  # Отображение названия продукта в админке

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def get_average_rating(self):
        reviews = self.reviews.filter(is_active=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='Продукт')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name='Пользователь')
    rating = models.PositiveSmallIntegerField(verbose_name='Оценка')
    comment = models.TextField(verbose_name='Комментарий', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_active = models.BooleanField(default=True, verbose_name='Активен')  # Для модерации отзывов

    def __str__(self):
        return f'Отзыв от {self.user.username} на {self.product.name}'

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
