import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from config import SCRAPER_CONFIG
import pandas as pd

def check_products():
    """Проверка продуктов в базе данных и Excel"""
    print("\nПодключение к базе данных...")
    
    db = DatabaseManager()
    
    # Проверяем данные в базе
    products_query = """
    SELECT name, price, url, created_at, author
    FROM products
    ORDER BY created_at DESC
    LIMIT 5
    """
    
    products = db.execute_query(products_query)
    
    print(f"\nВсего продуктов в базе: {len(products)}")
    
    print("\nПоследние добавленные продукты:")
    print("-" * 80)
    for product in products:
        print(f"Название: {product['name']}")
        print(f"Автор: {product['author'] if product['author'] else 'Не указан'}")
        print(f"Цена: ${product['price']}" if product['price'] else "Цена: Не указана")
        print(f"URL: {product['url']}")
        print(f"Добавлен: {product['created_at']}")
        print("-" * 80)
    
    # Статистика по ценам
    stats_query = """
    SELECT 
        COUNT(*) as total,
        COUNT(price) as with_price,
        AVG(price) as avg_price,
        MIN(price) as min_price,
        MAX(price) as max_price
    FROM products
    WHERE price IS NOT NULL
    """
    
    stats = db.execute_query(stats_query, fetch_one=True)
    
    print("\nСтатистика по ценам:")
    print(f"Всего продуктов с ценой: {stats['with_price']} из {stats['total']}")
    print(f"Средняя цена: ${stats['avg_price']:.2f}")
    print(f"Минимальная цена: ${stats['min_price']}")
    print(f"Максимальная цена: ${stats['max_price']}")
    
    # Проверяем данные в Excel
    excel_file = SCRAPER_CONFIG['excel_output']
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
        print(f"\nДанные в Excel файле ({excel_file}):")
        print(f"Всего записей: {len(df)}")
        print("\nПоследние 3 записи:")
        print(df.tail(3)[['name', 'author', 'price', 'url']].to_string())
    else:
        print(f"\nExcel файл не найден: {excel_file}")

if __name__ == "__main__":
    check_products() 