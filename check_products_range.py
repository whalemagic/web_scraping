import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime

def check_products_range():
    try:
        # Загружаем параметры подключения из .env
        load_dotenv()
        
        # Подключаемся к базе данных
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Получаем последние 10 продуктов
        cursor.execute("""
            SELECT name, author, price, url, created_at 
            FROM products 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        products = cursor.fetchall()
        
        print("\nПоследние 10 добавленных продуктов:")
        print("-" * 80)
        for product in products:
            print(f"Название: {product['name']}")
            print(f"Автор: {product['author']}")
            print(f"Цена: {product['price']}")
            print(f"URL: {product['url']}")
            print(f"Добавлен: {product['created_at']}")
            print("-" * 80)
        
        # Получаем минимальную и максимальную страницу
        cursor.execute("""
            SELECT 
                MIN(CAST(SUBSTRING(url FROM 'p/([0-9]+)') AS INTEGER)) as min_page,
                MAX(CAST(SUBSTRING(url FROM 'p/([0-9]+)') AS INTEGER)) as max_page
            FROM products
        """)
        
        page_range = cursor.fetchone()
        print("\nДиапазон страниц:")
        print(f"Минимальная страница: {page_range['min_page']}")
        print(f"Максимальная страница: {page_range['max_page']}")
        
    except Exception as e:
        print(f"Ошибка при проверке продуктов: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    check_products_range() 