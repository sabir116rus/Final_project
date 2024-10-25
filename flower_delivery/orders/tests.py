# orders/tests.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Product
from .models import Order, OrderItem
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from unittest.mock import patch  # Импортируем patch


class CartTest(TestCase):
    def setUp(self):
        # Создаём пользователя
        self.user = User.objects.create_user(username='testuser', password='TestPassword123')
        # Создаём продукт
        self.product = Product.objects.create(
            name='Тестовый Букет',
            price=1999.99,
            image=SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg'),
        )

    def test_cart_add(self):
        """
        Проверяем, что товар добавляется в корзину.
        """
        response = self.client.post(reverse('cart_add', args=[self.product.id]))
        self.assertRedirects(response, reverse('product_list'))
        # Проверяем, что товар добавлен в сессию
        cart = self.client.session.get('cart')
        self.assertIsNotNone(cart)
        self.assertIn(str(self.product.id), cart)
        self.assertEqual(cart[str(self.product.id)]['quantity'], 1)
        self.assertEqual(float(cart[str(self.product.id)]['price']), self.product.price)

    def test_cart_remove(self):
        """
        Проверяем, что товар удаляется из корзины.
        """
        # Добавляем товар в корзину
        self.client.post(reverse('cart_add', args=[self.product.id]))
        # Удаляем товар из корзины
        response = self.client.post(reverse('cart_remove', args=[self.product.id]))
        self.assertRedirects(response, reverse('cart_detail'))
        # Проверяем, что корзина пуста
        cart = self.client.session.get('cart')
        self.assertNotIn(str(self.product.id), cart)


class OrderCreateTest(TestCase):
    def setUp(self):
        # Создаём пользователя и логинимся
        self.user = User.objects.create_user(username='testuser', password='TestPassword123')
        self.client.login(username='testuser', password='TestPassword123')
        # Создаём продукт
        self.product = Product.objects.create(
            name='Тестовый Букет',
            price=1999.99,
            image=SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg'),
        )
        # Добавляем товар в корзину
        self.client.post(reverse('cart_add', args=[self.product.id]))

    @patch('orders.views.send_order_notification')  # Мокаем функцию отправки уведомления
    def test_order_create_get(self, mock_send_notification):
        """
        Проверяем доступность страницы оформления заказа.
        """
        response = self.client.get(reverse('order_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/order_create.html')

    @patch('orders.views.send_order_notification')  # Мокаем функцию отправки уведомления
    def test_order_create_post(self, mock_send_notification):
        """
        Проверяем процесс создания заказа.
        """
        response = self.client.post(reverse('order_create'), {
            'address': 'Test Address 123',
            'phone': '1234567890',
            'comment': 'Test comment'  # Добавляем комментарий, если он обязательный
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/order_created.html')

        # Проверяем, что заказ создан
        order = Order.objects.get(user=self.user)

        # Приводим цену к нужной точности
        self.assertEqual(order.total_price.quantize(Decimal('0.01')),
                         Decimal(self.product.price).quantize(Decimal('0.01')))

        self.assertEqual(order.address, 'Test Address 123')
        self.assertEqual(order.phone, '1234567890')
        self.assertEqual(order.status, 'pending')

        # Проверяем, что OrderItem создан
        order_item = OrderItem.objects.get(order=order, product=self.product)
        self.assertEqual(order_item.quantity, 1)
        self.assertEqual(order_item.price.quantize(Decimal('0.01')), Decimal(self.product.price).quantize(Decimal('0.01')))

        # Проверяем, что корзина очищена
        cart = self.client.session.get('cart')
        self.assertIsNone(cart)

        # Проверяем, что функция отправки уведомления была вызвана
        mock_send_notification.assert_called_once_with(order)

    @patch('orders.views.send_order_notification')  # Мокаем функцию отправки уведомления
    def test_order_create_redirect_if_cart_empty(self, mock_send_notification):
        """
        Проверяем, что при пустой корзине происходит редирект на страницу каталога.
        """
        # Очистка корзины
        session = self.client.session
        session['cart'] = {}
        session.save()
        response = self.client.get(reverse('order_create'))
        self.assertRedirects(response, reverse('product_list'))
        # Проверяем, что функция отправки уведомления не была вызвана
        mock_send_notification.assert_not_called()


class OrderStatusTest(TestCase):
    def setUp(self):
        # Создаём пользователя и логинимся
        self.user = User.objects.create_user(username='testuser', password='TestPassword123')
        self.admin_user = User.objects.create_superuser(username='admin', password='AdminPassword123',
                                                        email='admin@example.com')
        # Создаём продукт
        self.product = Product.objects.create(
            name='Тестовый Букет',
            price=1999.99,
            image=SimpleUploadedFile(name='test_image.jpg', content=b'', content_type='image/jpeg'),
        )
        # Создаём заказ
        self.order = Order.objects.create(
            user=self.user,
            status='pending',
            total_price=self.product.price,
            address='Test Address 123',
            phone='1234567890'
        )
        # Создаём OrderItem
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=self.product.price,
            quantity=1
        )

    @patch('orders.models.send_status_change_notification')  # Мокаем функцию отправки уведомления
    def test_admin_can_change_order_status(self, mock_send_status_notification):
        """
        Проверяем, что администратор может изменять статус заказа.
        """
        # Логинимся как администратор
        self.client.login(username='admin', password='AdminPassword123')

        # Формируем POST-запрос для изменения статуса, добавляем нужные скрытые поля для формы
        url = reverse('admin:orders_order_change', args=[self.order.id])
        post_data = {
            'user': self.user.id,
            'status': 'accepted',  # Новый статус
            'total_price': self.order.total_price,
            'address': self.order.address,
            'phone': self.order.phone,
            # Management form fields для inline OrderItem
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '1',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            # Данные для существующего OrderItem
            'items-0-id': self.order_item.id,
            'items-0-order': self.order.id,
            'items-0-product': self.product.id,
            'items-0-quantity': self.order_item.quantity,
            'items-0-price': self.order_item.price,
        }

        response = self.client.post(url, post_data, follow=True)

        # Проверка, что статус изменён
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'accepted')  # Проверяем, что статус изменился
        self.assertEqual(response.status_code, 200)

        # Проверяем, что функция отправки уведомления была вызвана
        mock_send_status_notification.assert_called_once_with(self.order)