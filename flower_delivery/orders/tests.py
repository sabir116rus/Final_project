# orders/tests.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Product
from .models import Order, OrderItem
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from unittest.mock import patch
from datetime import datetime, time


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


class CartUpdateTest(TestCase):
    def setUp(self):
        # Создаём пользователя
        self.user = User.objects.create_user(username='testuser', password='TestPassword123')
        # Создаём продукты
        self.product1 = Product.objects.create(
            name='Тестовый Букет 1',
            price=1000.00,
            image=SimpleUploadedFile(name='test_image1.jpg', content=b'', content_type='image/jpeg'),
        )
        self.product2 = Product.objects.create(
            name='Тестовый Букет 2',
            price=2000.00,
            image=SimpleUploadedFile(name='test_image2.jpg', content=b'', content_type='image/jpeg'),
        )
        # Добавляем товары в корзину
        self.client.post(reverse('cart_add', args=[self.product1.id]))
        self.client.post(reverse('cart_add', args=[self.product2.id]))

    def test_cart_update_increase_quantity(self):
        """
        Проверяем увеличение количества товара в корзине.
        """
        response = self.client.post(reverse('cart_update'), {
            f'quantity_{self.product1.id}': 3,
            f'quantity_{self.product2.id}': 2,
        })
        self.assertRedirects(response, reverse('cart_detail'))
        cart = self.client.session.get('cart')
        self.assertEqual(cart[str(self.product1.id)]['quantity'], 3)
        self.assertEqual(cart[str(self.product2.id)]['quantity'], 2)

    def test_cart_update_decrease_quantity(self):
        """
        Проверяем уменьшение количества товара в корзине.
        """
        response = self.client.post(reverse('cart_update'), {
            f'quantity_{self.product1.id}': 1,
            f'quantity_{self.product2.id}': 1,
        })
        self.assertRedirects(response, reverse('cart_detail'))
        cart = self.client.session.get('cart')
        self.assertEqual(cart[str(self.product1.id)]['quantity'], 1)
        self.assertEqual(cart[str(self.product2.id)]['quantity'], 1)

    def test_cart_update_remove_item_when_zero(self):
        """
        Проверяем удаление товара из корзины при установке количества в 0.
        """
        response = self.client.post(reverse('cart_update'), {
            f'quantity_{self.product1.id}': 0,
            f'quantity_{self.product2.id}': 2,
        })
        self.assertRedirects(response, reverse('cart_detail'))
        cart = self.client.session.get('cart')
        self.assertNotIn(str(self.product1.id), cart)
        self.assertEqual(cart[str(self.product2.id)]['quantity'], 2)

    def test_cart_update_invalid_quantity(self):
        """
        Проверяем обработку некорректных значений количества.
        """
        response = self.client.post(reverse('cart_update'), {
            f'quantity_{self.product1.id}': 'invalid',
            f'quantity_{self.product2.id}': -1,
        })
        self.assertRedirects(response, reverse('cart_detail'))
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Введите корректное количество для товара' in str(message) for message in messages))
        # Проверяем, что количество товара1 не изменилось
        cart = self.client.session.get('cart')
        self.assertEqual(cart[str(self.product1.id)]['quantity'], 1)  # Изначально было 1
        # Товар2 должен быть удален, т.к. количество -1
        self.assertNotIn(str(self.product2.id), cart)


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
            'comment': 'Test comment',  # Добавляем комментарий, если он обязательный
            'delivery_date': '2024-12-25',
            'delivery_time': '14:30',
            'delivery_place': 'Front Door',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/order_created.html')

        # Проверяем, что заказ создан
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total_price.quantize(Decimal('0.01')),
                         Decimal(self.product.price).quantize(Decimal('0.01')))
        self.assertEqual(order.address, 'Test Address 123')
        self.assertEqual(order.phone, '1234567890')
        self.assertEqual(order.comment, 'Test comment')
        self.assertEqual(order.delivery_date.strftime('%Y-%m-%d'), '2024-12-25')
        self.assertEqual(order.delivery_time.strftime('%H:%M'), '14:30')
        self.assertEqual(order.delivery_place, 'Front Door')
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

    def test_order_create_time_restriction(self):
        """
        Проверяем, что заказы принимаются только с 1:00 до 23:00.
        """
        with patch('orders.views.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 30)  # 00:30, до 1:00
            response = self.client.post(reverse('order_create'), {
                'address': 'Test Address 123',
                'phone': '1234567890',
                'comment': 'Test comment',
                'delivery_date': '2024-12-25',
                'delivery_time': '14:30',
                'delivery_place': 'Front Door',
            })
            self.assertRedirects(response, reverse('cart_detail'))
            messages = list(response.wsgi_request._messages)
            self.assertTrue(any('Извините, заказы принимаются только с 1:00 до 23:00.' in str(message) for message in messages))
            # Проверяем, что заказ не создан
            self.assertFalse(Order.objects.filter(user=self.user).exists())

        with patch('orders.views.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 23, 30)  # 23:30, после 23:00
            response = self.client.post(reverse('order_create'), {
                'address': 'Test Address 123',
                'phone': '1234567890',
                'comment': 'Test comment',
                'delivery_date': '2024-12-25',
                'delivery_time': '14:30',
                'delivery_place': 'Front Door',
            })
            self.assertRedirects(response, reverse('cart_detail'))
            messages = list(response.wsgi_request._messages)
            self.assertTrue(any('Извините, заказы принимаются только с 1:00 до 23:00.' in str(message) for message in messages))
            # Проверяем, что заказ не создан
            self.assertFalse(Order.objects.filter(user=self.user).exists())


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


class OrderItemTest(TestCase):
    def setUp(self):
        # Создаём пользователя
        self.user = User.objects.create_user(username='testuser', password='TestPassword123')
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
            total_price=1999.99,
            address='Test Address 123',
            phone='1234567890'
        )
        # Создаём OrderItem
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=self.product.price,
            quantity=2
        )

    def test_order_item_str(self):
        """
        Тестирование метода __str__ модели OrderItem.
        """
        self.assertEqual(str(self.order_item), f'{self.product.name} x {self.order_item.quantity}')

    def test_get_cost(self):
        """
        Тестирование метода get_cost модели OrderItem.
        """
        expected_cost = Decimal('3999.98')
        actual_cost = Decimal(self.order_item.get_cost()).quantize(Decimal('0.01'))  # Преобразуем в Decimal перед quantize
        self.assertEqual(actual_cost, expected_cost)