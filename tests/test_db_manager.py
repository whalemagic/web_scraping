import unittest
from pathlib import Path
import sys
import os

# Добавляем путь к корневой директории проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        """Подготовка к каждому тесту."""
        self.db = DatabaseManager()
        self.db.connect()
        
        # Тестовые данные
        self.test_product = {
            'name': 'Тестовый продукт',
            'price': 999.99,
            'url': 'https://example.com/product',
            'image_url': 'https://example.com/image.jpg',
            'description': 'Тестовое описание',
            'category': 'Тестовая категория'
        }
    
    def tearDown(self):
        """Очистка после каждого теста."""
        self.db.disconnect()

    def test_connection(self):
        """Тест подключения к базе данных."""
        self.assertIsNotNone(self.db.conn)
        self.assertIsNotNone(self.db.cur)

    def test_add_product(self):
        """Тест добавления продукта."""
        # Добавляем продукт
        product_id = self.db.add_product(self.test_product)
        
        # Проверяем, что ID присвоен
        self.assertIsInstance(product_id, int)
        
        # Получаем продукт и проверяем его данные
        product = self.db.get_product(product_id)
        self.assertEqual(product['name'], self.test_product['name'])
        self.assertEqual(float(product['price']), self.test_product['price'])
        
        # Очищаем тестовые данные
        self.db.delete_product(product_id)

    def test_update_product(self):
        """Тест обновления продукта."""
        # Добавляем продукт
        product_id = self.db.add_product(self.test_product)
        
        # Обновляем данные
        updated_data = {
            'name': 'Обновленный продукт',
            'price': 1999.99
        }
        success = self.db.update_product(product_id, updated_data)
        
        # Проверяем успешность обновления
        self.assertTrue(success)
        
        # Получаем обновленный продукт
        product = self.db.get_product(product_id)
        self.assertEqual(product['name'], updated_data['name'])
        self.assertEqual(float(product['price']), updated_data['price'])
        
        # Очищаем тестовые данные
        self.db.delete_product(product_id)

    def test_delete_product(self):
        """Тест удаления продукта."""
        # Добавляем продукт
        product_id = self.db.add_product(self.test_product)
        
        # Удаляем продукт
        success = self.db.delete_product(product_id)
        self.assertTrue(success)
        
        # Проверяем, что продукт удален
        product = self.db.get_product(product_id)
        self.assertIsNone(product)

    def test_search_products(self):
        """Тест поиска продуктов."""
        # Добавляем несколько продуктов
        product_ids = []
        products = [
            {
                'name': 'Продукт 1',
                'price': 100,
                'category': 'Категория A'
            },
            {
                'name': 'Продукт 2',
                'price': 200,
                'category': 'Категория B'
            },
            {
                'name': 'Другой продукт',
                'price': 150,
                'category': 'Категория A'
            }
        ]
        
        for product in products:
            product_ids.append(self.db.add_product(product))
        
        try:
            # Поиск по имени
            results = self.db.search_products(name='Продукт')
            self.assertEqual(len(results), 2)
            
            # Поиск по категории
            results = self.db.search_products(category='Категория A')
            self.assertEqual(len(results), 2)
            
            # Поиск по цене
            results = self.db.search_products(min_price=150, max_price=200)
            self.assertEqual(len(results), 2)
            
        finally:
            # Очищаем тестовые данные
            for product_id in product_ids:
                self.db.delete_product(product_id)

    def test_validation(self):
        """Тест валидации данных."""
        # Тест на отсутствие названия
        with self.assertRaises(ValueError):
            self.db.add_product({'price': 100})
        
        # Тест на отрицательную цену
        with self.assertRaises(ValueError):
            self.db.add_product({
                'name': 'Тест',
                'price': -100
            })
        
        # Тест на некорректный URL
        with self.assertRaises(ValueError):
            self.db.add_product({
                'name': 'Тест',
                'url': 'некорректный-url'
            })

if __name__ == '__main__':
    unittest.main() 