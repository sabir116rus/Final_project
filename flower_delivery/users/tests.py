# users/tests.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, call  # Добавляем call
from orders.models import Order, OrderItem
from products.models import Product
from django.core.files.uploadedfile import SimpleUploadedFile


class UserRegistrationTest(TestCase):
    def test_register_url(self):
        """
        Проверяем, что страница регистрации доступна.
        """
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_register_form(self):
        """
        Тестируем процесс регистрации.
        Проверяем, что пользователь и профиль создаются.
        """
        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
            'phone': '1234567890',
            'address': 'Test Address 123'
        })
        # Проверяем редирект после успешной регистрации
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

        # Проверяем, что пользователь был создан
        user = User.objects.get(username='testuser')
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'testuser@example.com')

        # Проверяем, что профиль был создан
        profile = user.profile
        self.assertEqual(profile.phone, '1234567890')
        self.assertEqual(profile.address, 'Test Address 123')


class UserLoginTest(TestCase):
    def setUp(self):
        """
        Создаем пользователя для тестирования входа.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123'
        )

    def test_login_url(self):
        """
        Проверяем, что страница входа доступна.
        """
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_login(self):
        """
        Тестируем процесс входа.
        """
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'TestPassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('product_list'))

        # Проверяем, что пользователь вошел в систему
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, 'testuser')


class UserLogoutTest(TestCase):
    def setUp(self):
        """
        Создаем пользователя и входим в систему для тестирования выхода.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123'
        )
        self.client.login(username='testuser', password='TestPassword123')

    def test_logout(self):
        """
        Тестируем процесс выхода.
        """
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

        # Проверяем, что пользователь вышел из системы
        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)


class UserProfileTest(TestCase):
    def setUp(self):
        """
        Создаем пользователя и входим в систему для тестирования профиля.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123'
        )
        self.client.login(username='testuser', password='TestPassword123')

    def test_profile_access(self):
        """
        Проверяем, что авторизованный пользователь может получить доступ к профилю.
        """
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_redirect_for_anonymous(self):
        """
        Проверяем, что неавторизованного пользователя перенаправляет на страницу входа.
        """
        self.client.logout()
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f'{reverse("login")}?next={reverse("profile")}')

    @patch('users.views.Cart')  # Мокаем класс Cart в users.views
    def test_reorder_adds_items_to_cart(self, mock_cart_class):
        """
        Проверяем, что повторный заказ добавляет товары в корзину.
        """
        # Создаём заказ с несколькими товарами
        product1 = Product.objects.create(
            name='Тестовый Букет 1',
            price=1000.00,
            image=SimpleUploadedFile(name='test_image1.jpg', content=b'', content_type='image/jpeg'),
            available=True
        )
        product2 = Product.objects.create(
            name='Тестовый Букет 2',
            price=2000.00,
            image=SimpleUploadedFile(name='test_image2.jpg', content=b'', content_type='image/jpeg'),
            available=True
        )
        order = Order.objects.create(
            user=self.user,
            status='completed',
            total_price=3000.00,
            address='Test Address 123',
            phone='1234567890'
        )
        OrderItem.objects.create(
            order=order,
            product=product1,
            price=1000.00,
            quantity=2
        )
        OrderItem.objects.create(
            order=order,
            product=product2,
            price=2000.00,
            quantity=1
        )

        # Настраиваем mock для Cart
        mock_cart = mock_cart_class.return_value
        # Нет необходимости дополнительно патчить 'orders.cart.Cart.add'

        # Выполняем запрос на повторный заказ
        response = self.client.get(reverse('reorder', args=[order.id]))
        self.assertRedirects(response, reverse('cart_detail'))

        # Проверяем, что метод add был вызван для каждого доступного товара с правильными аргументами
        expected_calls = [
            call(product=product1, quantity=2),
            call(product=product2, quantity=1),
        ]
        mock_cart.add.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_cart.add.call_count, 2)

        # Проверяем, что сообщения об успешном добавлении отображаются
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('добавлены в корзину' in str(message) for message in messages))

    @patch('users.views.Cart')  # Мокаем класс Cart в users.views
    def test_reorder_with_unavailable_product(self, mock_cart_class):
        """
        Проверяем, что недоступные товары не добавляются в корзину при повторном заказе.
        """
        # Создаём заказ с одним доступным и одним недоступным товаром
        product1 = Product.objects.create(
            name='Тестовый Букет 1',
            price=1000.00,
            image=SimpleUploadedFile(name='test_image1.jpg', content=b'', content_type='image/jpeg'),
            available=True
        )
        product2 = Product.objects.create(
            name='Тестовый Букет 2',
            price=2000.00,
            image=SimpleUploadedFile(name='test_image2.jpg', content=b'', content_type='image/jpeg'),
            available=False  # Один из продуктов недоступен
        )
        order = Order.objects.create(
            user=self.user,
            status='completed',
            total_price=3000.00,
            address='Test Address 123',
            phone='1234567890'
        )
        OrderItem.objects.create(
            order=order,
            product=product1,
            price=1000.00,
            quantity=1
        )
        OrderItem.objects.create(
            order=order,
            product=product2,
            price=2000.00,
            quantity=1
        )

        # Настраиваем mock для Cart
        mock_cart = mock_cart_class.return_value
        # Нет необходимости дополнительно патчить 'orders.cart.Cart.add'

        # Выполняем запрос на повторный заказ
        response = self.client.get(reverse('reorder', args=[order.id]))
        self.assertRedirects(response, reverse('cart_detail'))

        # Проверяем, что метод add был вызван только для доступного товара с правильными аргументами
        expected_calls = [
            call(product=product1, quantity=1),
        ]
        mock_cart.add.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_cart.add.call_count, 1)

        # Проверяем, что сообщение о недоступном товаре отображается
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('недоступен и не был добавлен в корзину' in str(message) for message in messages))

class ReorderTest(TestCase):
    def setUp(self):
        # Создаём пользователя и логинимся
        self.user = User.objects.create_user(username='testuser', password='TestPassword123')
        self.client.login(username='testuser', password='TestPassword123')
        # Создаём продукты
        self.product1 = Product.objects.create(
            name='Тестовый Букет 1',
            price=1000.00,
            image=SimpleUploadedFile(name='test_image1.jpg', content=b'', content_type='image/jpeg'),
            available=True
        )
        self.product2 = Product.objects.create(
            name='Тестовый Букет 2',
            price=2000.00,
            image=SimpleUploadedFile(name='test_image2.jpg', content=b'', content_type='image/jpeg'),
            available=True
        )
        # Создаём заказ
        self.order = Order.objects.create(
            user=self.user,
            status='completed',
            total_price=3000.00,
            address='Test Address 123',
            phone='1234567890'
        )
        # Создаём OrderItems
        OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            price=1000.00,
            quantity=2
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            price=2000.00,
            quantity=1
        )

    @patch('orders.cart.Cart.add')  # Мокаем метод add класса Cart
    def test_reorder_adds_items_to_cart(self, mock_cart_add):
        """
        Проверяем, что повторный заказ добавляет товары в корзину.
        """
        response = self.client.get(reverse('reorder', args=[self.order.id]))
        self.assertRedirects(response, reverse('cart_detail'))

        # Проверяем, что метод add был вызван для каждого доступного товара с правильными аргументами
        expected_calls = [
            call(product=self.product1, quantity=2),
            call(product=self.product2, quantity=1),
        ]
        mock_cart_add.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_cart_add.call_count, 2)

        # Проверяем, что сообщение об успешном добавлении отображается
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('добавлены в корзину' in str(message) for message in messages))

    @patch('orders.cart.Cart.add')  # Мокаем метод add класса Cart
    def test_reorder_with_unavailable_product(self, mock_cart_add):
        """
        Проверяем, что недоступные товары не добавляются в корзину при повторном заказе.
        """
        # Устанавливаем один продукт как недоступный
        self.product2.available = False
        self.product2.save()

        response = self.client.get(reverse('reorder', args=[self.order.id]))
        self.assertRedirects(response, reverse('cart_detail'))

        # Проверяем, что метод add был вызван только для доступного товара с правильными аргументами
        expected_calls = [
            call(product=self.product1, quantity=2),
        ]
        mock_cart_add.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_cart_add.call_count, 1)

        # Проверяем, что сообщение о недоступном товаре отображается
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('недоступен и не был добавлен в корзину' in str(message) for message in messages))

class ReorderIntegrationTest(TestCase):
    def setUp(self):
        # Создаём пользователя и логинимся
        self.user = User.objects.create_user(username='testuser', password='TestPassword123')
        self.client.login(username='testuser', password='TestPassword123')
        # Создаём продукты
        self.product1 = Product.objects.create(
            name='Тестовый Букет 1',
            price=1000.00,
            image=SimpleUploadedFile(name='test_image1.jpg', content=b'', content_type='image/jpeg'),
            available=True
        )
        self.product2 = Product.objects.create(
            name='Тестовый Букет 2',
            price=2000.00,
            image=SimpleUploadedFile(name='test_image2.jpg', content=b'', content_type='image/jpeg'),
            available=True
        )
        # Создаём заказ
        self.order = Order.objects.create(
            user=self.user,
            status='completed',
            total_price=3000.00,
            address='Test Address 123',
            phone='1234567890'
        )
        # Создаём OrderItems
        OrderItem.objects.create(
            order=self.order,
            product=self.product1,
            price=1000.00,
            quantity=2
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product2,
            price=2000.00,
            quantity=1
        )

    def test_reorder_view(self):
        """
        Интеграционный тест для повторного заказа: проверяем, что товары добавляются в корзину.
        """
        response = self.client.get(reverse('reorder', args=[self.order.id]))
        self.assertRedirects(response, reverse('cart_detail'))
        # Проверяем содержимое корзины
        session = self.client.session
        cart = session.get('cart')
        self.assertIsNotNone(cart)
        self.assertIn(str(self.product1.id), cart)
        self.assertIn(str(self.product2.id), cart)
        self.assertEqual(cart[str(self.product1.id)]['quantity'], 2)
        self.assertEqual(cart[str(self.product2.id)]['quantity'], 1)
