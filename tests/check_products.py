import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from config import SCRAPER_CONFIG
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_products():
    """Проверка продуктов в базе данных"""
    try:
        # Подключаемся к базе данных
        db = DatabaseManager()
        db.connect()
        logger.info("Подключение к базе данных...")

        # Получаем все продукты
        query = """
        SELECT id, name, author, price, url, image_url, description, categories, 
               created_at, updated_at 
        FROM products 
        ORDER BY created_at DESC
        """
        products = db.execute_query(query)

        if not products:
            print("В базе данных нет продуктов")
            return

        print(f"\nВсего продуктов в базе: {len(products)}\n")
        print("Последние добавленные продукты:")
        
        for product in products:
            print("-" * 80)
            print(f"ID: {product['id']}")
            print(f"Название: {product['name']}")
            print(f"Автор: {product['author']}")
            print(f"Цена: ${product['price']}")
            print(f"URL: {product['url']}")
            print(f"URL изображения: {product['image_url']}")
            print(f"Описание: {product['description']}")
            print(f"Категории: {product['categories']}")
            print(f"Добавлен: {product['created_at']}")
            print(f"Обновлен: {product['updated_at']}")
            print("-" * 80 + "\n")

        db.disconnect()
        logger.info("Соединение с базой данных закрыто")

    except Exception as e:
        logger.error(f"Ошибка при проверке продуктов: {e}")

if __name__ == "__main__":
    check_products() 