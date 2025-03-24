import sys
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
    
    # Получаем общее количество продуктов
    cur.execute("SELECT COUNT(*) as total FROM products")
    total = cur.fetchone()['total']
    print(f"\nВсего продуктов в базе: {total}")
    
    # Получаем последние 5 добавленных продуктов
    cur.execute("""
        SELECT name, price, url, created_at 
        FROM products 
        ORDER BY created_at DESC 
        LIMIT 5
    """)
    products = cur.fetchall()
    
    print("\nПоследние добавленные продукты:")
    print("-" * 80)
    for product in products:
        print(f"Название: {product['name']}")
        print(f"Цена: ${product['price']}" if product['price'] else "Цена: Не указана")
        print(f"URL: {product['url']}")
        print(f"Добавлен: {product['created_at']}")
        print("-" * 80)
    
    # Статистика по ценам
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(price) as with_price,
            ROUND(AVG(price)::numeric, 2) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM products
        WHERE price IS NOT NULL
    """)
    stats = cur.fetchone()
    
    print("\nСтатистика по ценам:")
    print(f"Всего продуктов с ценой: {stats['with_price']} из {stats['total']}")
    print(f"Средняя цена: ${stats['avg_price']}")
    print(f"Минимальная цена: ${stats['min_price']}")
    print(f"Максимальная цена: ${stats['max_price']}")
    
except Exception as e:
    print(f"\nОшибка при работе с базой данных: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close() 