# products/tests.py

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Product

from django.urls import reverse


class ProductModelTest(TestCase):
    def setUp(self):
        """
        Метод setUp запускается перед каждым тестом.
        Здесь мы создаем тестовый экземпляр модели Product.
        """
        # Создаем простой загруженный файл для поля image
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',  # Пустой контент, т.к. для тестов он не требуется
            content_type='image/jpeg'
        )

        # Создаем экземпляр продукта
        self.product = Product.objects.create(
            name='Тестовый Букет',
            price=1999.99,
            image=image,
        )

    # products/tests.py

    def test_product_creation(self):
        """
        Тестирование создания продукта.
        Проверяем, что продукт успешно создан и сохранен в базе данных.
        """
        self.assertEqual(self.product.name, 'Тестовый Букет')
        self.assertEqual(self.product.price, 1999.99)

        # Проверяем, что имя файла изображения содержит 'test_image.jpg',
        # но не обязательно совпадает полностью, так как имя файла может быть изменено
        self.assertIn('test_image.jpg', self.product.image.url)

    def test_product_creation(self):
        """
        Тестирование создания продукта.
        Проверяем, что продукт успешно создан и сохранен в базе данных.
        """
        self.assertEqual(self.product.name, 'Тестовый Букет')
        self.assertEqual(self.product.price, 1999.99)

        # Проверяем, что URL изображения корректен
        self.assertIn('products/', self.product.image.url)  # Проверка части пути

    def test_product_str(self):
        """
        Тестирование метода __str__ модели Product.
        Проверяем, что строковое представление продукта соответствует его названию.
        """
        self.assertEqual(str(self.product), 'Тестовый Букет')


class ProductListViewTest(TestCase):
    def setUp(self):
        """
        Создаем несколько продуктов для тестирования отображения в представлении.
        """
        # Создаем несколько продуктов
        Product.objects.create(
            name='Букет Роз',
            price=1500.00,
            image=SimpleUploadedFile(name='rose.jpg', content=b'', content_type='image/jpeg'),
        )
        Product.objects.create(
            name='Букет Лилий',
            price=1800.00,
            image=SimpleUploadedFile(name='lily.jpg', content=b'', content_type='image/jpeg'),
        )

    def test_product_list_view_status_code(self):
        """
        Проверяем, что представление возвращает статус 200 (OK).
        """
        url = reverse('product_list')  # Имя маршрута, определенное в urls.py
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_product_list_view_template_used(self):
        """
        Проверяем, что представление использует правильный шаблон.
        """
        url = reverse('product_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'products/product_list.html')

    def test_product_list_view_context(self):
        """
        Проверяем, что представление передает правильный контекст.
        """
        url = reverse('product_list')
        response = self.client.get(url)
        self.assertIn('products', response.context)
        self.assertEqual(len(response.context['products']), 2)
        # Проверяем, что названия продуктов соответствуют созданным
        product_names = [product.name for product in response.context['products']]
        self.assertIn('Букет Роз', product_names)
        self.assertIn('Букет Лилий', product_names)

    def test_product_list_view_html_content(self):
        """
        Проверяем, что HTML содержит информацию о продуктах с ценами в русском формате (с запятой).
        """
        url = reverse('product_list')
        response = self.client.get(url)

        # Ожидаемая строка с запятой в формате цены
        self.assertContains(response, 'Цена: 1500,00 руб.')
        self.assertContains(response, 'Цена: 1800,00 руб.')

