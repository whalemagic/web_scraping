import os
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Параметры подключения
params = {
    'dbname': 'magic_products_db',
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

try:
    # Подключаемся к базе
    print("\nПодключение к базе данных...")
    conn = psycopg2.connect(**params)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Проверяем количество записей
    cur.execute("SELECT COUNT(*) as count FROM products")
    count = cur.fetchone()['count']
    print(f"\nКоличество записей в таблице products: {count}")
    
    if count > 0:
        # Получаем последние 5 записей
        cur.execute("""
            SELECT id, name, price, url, created_at 
            FROM products 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        products = cur.fetchall()
        
        print("\nПоследние добавленные продукты:")
        print("-" * 80)
        for product in products:
            print(f"ID: {product['id']}")
            print(f"Название: {product['name']}")
            print(f"Цена: ${product['price']}" if product['price'] else "Цена: Не указана")
            print(f"URL: {product['url']}")
            print(f"Добавлен: {product['created_at']}")
            print("-" * 80)
    else:
        print("\nВ таблице products нет данных")
    
except Exception as e:
    print(f"\nОшибка при работе с базой данных: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close() 