# products/models.py

from django.db import models

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