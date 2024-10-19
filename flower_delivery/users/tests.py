# users/tests.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

# users/tests.py

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

# users/tests.py

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

# users/tests.py

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

# users/tests.py

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
