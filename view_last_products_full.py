import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv

def view_last_products_full():
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
        
        # Получаем последние 10 записей со всеми колонками
        cursor.execute("""
            SELECT * 
            FROM products 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        products = cursor.fetchall()
        
        print("\nПоследние 10 добавленных продуктов:")
        print("=" * 100)
        for product in products:
            print(f"ID: {product['id']}")
            print(f"Название: {product['name']}")
            print(f"Автор: {product['author']}")
            print(f"Цена: ${product['price']}")
            print(f"URL: {product['url']}")
            print(f"URL изображения: {product['image_url']}")
            print(f"Описание: {product['description']}")
            print(f"Категории: {product['categories']}")
            print(f"Создан: {product['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Обновлен: {product['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 100)
            
    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    view_last_products_full() 