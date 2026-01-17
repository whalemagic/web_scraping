import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import re
from urllib.parse import urlparse
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, env_path: Optional[Path] = None):
        """
        Инициализация менеджера базы данных.
        
        Args:
            env_path (Path, optional): Путь к файлу с переменными окружения
        """
        if env_path is None:
            env_path = Path(__file__).parent.parent / '.env'
        
        load_dotenv(env_path, override=True)
        
        self.params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }
        
        self.conn = None
        self.cur = None
        self.connect()

    def connect(self) -> None:
        """Установка соединения с базой данных."""
        try:
            self.conn = psycopg2.connect(**self.params)
            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info("Успешное подключение к базе данных")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def disconnect(self) -> None:
        """Закрытие соединения с базой данных."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")

    def __enter__(self):
        """Контекстный менеджер для автоматического подключения."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер для автоматического отключения."""
        self.disconnect()

    @staticmethod
    def validate_product_data(data: Dict[str, Any]) -> None:
        """
        Валидация данных продукта перед добавлением/обновлением.
        
        Args:
            data (dict): Данные продукта
            
        Raises:
            ValueError: Если данные невалидны
        """
        if 'name' not in data or not data['name'].strip():
            raise ValueError("Название продукта обязательно")

        if 'price' in data and data['price'] is not None:
            if not isinstance(data['price'], (int, float)) or data['price'] < 0:
                raise ValueError("Цена должна быть положительным числом")

        if 'url' in data and data['url']:
            try:
                result = urlparse(data['url'])
                if not all([result.scheme, result.netloc]):
                    raise ValueError("Некорректный URL")
            except Exception:
                raise ValueError("Некорректный URL")

    def add_product(self, product_data: Dict[str, Any]) -> int:
        """
        Добавление продукта в базу данных.
        
        Args:
            product_data (dict): Данные продукта
            
        Returns:
            int: ID добавленного продукта
        """
        try:
            # Преобразуем одиночную категорию в массив
            categories = [product_data.get('category')] if product_data.get('category') else []
            
            # Формируем SQL запрос
            sql = """
                INSERT INTO products (
                    name, author, price, url, image_url, description, categories,
                    created_at, updated_at
                ) VALUES (
                    %(name)s, %(author)s, %(price)s, %(url)s, %(image_url)s,
                    %(description)s, %(categories)s, %(created_at)s, %(updated_at)s
                )
                RETURNING id
            """
            
            # Подготавливаем данные для вставки
            insert_data = {
                'name': product_data['name'],
                'author': product_data.get('author'),
                'price': product_data.get('price'),
                'url': product_data.get('url'),
                'image_url': product_data.get('image_url'),
                'description': product_data.get('description'),
                'categories': categories,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # Выполняем запрос
            self.cur.execute(sql, insert_data)
            product_id = self.cur.fetchone()['id']
            self.conn.commit()
            
            return product_id
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при добавлении продукта: {e}")
            raise

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение продукта по ID.
        
        Args:
            product_id (int): ID продукта
            
        Returns:
            dict: Данные продукта или None, если продукт не найден
        """
        try:
            sql = "SELECT * FROM products WHERE id = %s"
            self.cur.execute(sql, (product_id,))
            return self.cur.fetchone()
        except Exception as e:
            logger.error(f"Ошибка при получении продукта: {e}")
            return None

    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> bool:
        """
        Обновление данных продукта.
        
        Args:
            product_id (int): ID продукта
            product_data (dict): Новые данные продукта
            
        Returns:
            bool: True если обновление успешно, False если продукт не найден
        """
        self.validate_product_data(product_data)
        
        try:
            set_values = ', '.join([f"{k} = %s" for k in product_data.keys()])
            values = list(product_data.values()) + [product_id]
            query = f"UPDATE products SET {set_values} WHERE id = %s RETURNING id"
            
            self.cur.execute(query, values)
            updated = self.cur.fetchone()
            self.conn.commit()
            
            if updated:
                logger.info(f"Обновлен продукт с ID: {product_id}")
                return True
            else:
                logger.warning(f"Продукт с ID {product_id} не найден")
                return False
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при обновлении продукта: {e}")
            raise

    def delete_product(self, product_id: int) -> bool:
        """
        Удаление продукта по ID.
        
        Args:
            product_id (int): ID продукта
            
        Returns:
            bool: True если удаление успешно, False в противном случае
        """
        try:
            sql = "DELETE FROM products WHERE id = %s"
            self.cur.execute(sql, (product_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при удалении продукта: {e}")
            return False

    def search_products(self, 
                       name: Optional[str] = None,
                       category: Optional[str] = None,
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None,
                       limit: int = 100,
                       offset: int = 0) -> List[Dict[str, Any]]:
        """
        Поиск продуктов по различным критериям.
        
        Args:
            name (str, optional): Часть названия продукта
            category (str, optional): Категория продукта
            min_price (float, optional): Минимальная цена
            max_price (float, optional): Максимальная цена
            limit (int): Максимальное количество результатов
            offset (int): Смещение для пагинации
            
        Returns:
            List[dict]: Список найденных продуктов
        """
        conditions = []
        values = []
        
        if name:
            conditions.append("name ILIKE %s")
            values.append(f"%{name}%")
            
        if category:
            conditions.append("category = %s")
            values.append(category)
            
        if min_price is not None:
            conditions.append("price >= %s")
            values.append(min_price)
            
        if max_price is not None:
            conditions.append("price <= %s")
            values.append(max_price)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM products 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        try:
            self.cur.execute(query, values + [limit, offset])
            products = self.cur.fetchall()
            return [dict(p) for p in products]
            
        except Exception as e:
            logger.error(f"Ошибка при поиске продуктов: {e}")
            raise
            
    def insert_product(self, product_data: Dict[str, Any]) -> int:
        """
        Алиас для метода add_product для обратной совместимости.
        
        Args:
            product_data (dict): Данные продукта
            
        Returns:
            int: ID добавленного продукта
        """
        return self.add_product(product_data)

    def execute_query(self, query: str, params: tuple = None, fetch_one: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        Выполнение произвольного SQL запроса.
        
        Args:
            query (str): SQL запрос
            params (tuple, optional): Параметры запроса
            fetch_one (bool): Вернуть только одну запись
            
        Returns:
            list: Результат запроса
        """
        try:
            self.cur.execute(query, params)
            if fetch_one:
                return self.cur.fetchone()
            return self.cur.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            return None

    def save_product(self, product):
        """Сохраняет продукт в базу данных"""
        try:
            if not self.conn or self.conn.closed:
                self.connect()

            # Поддерживаем как 'tags', так и 'categories' для обратной совместимости
            tags = product.get('tags') or product.get('categories', [])
            discounted_price = product.get('discounted_price')
            reviews = product.get('reviews', [])
            
            self.cur.execute("""
                INSERT INTO products (
                    name, author, price, discounted_price, url, image_url, 
                    description, tags, reviews, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                product['name'],
                product.get('author'),
                product['price'],
                discounted_price,
                product['url'],
                product.get('image_url'),
                product.get('description'),
                tags,  # Используем tags вместо categories
                json.dumps(reviews) if reviews else None,  # Сохраняем reviews как JSON
                datetime.now(),
                datetime.now()
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при сохранении продукта: {e}")
            if self.conn:
                self.conn.rollback()
            raise 