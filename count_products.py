import psycopg2
import os
from dotenv import load_dotenv

def count_products():
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
        cursor = conn.cursor()
        
        # Подсчитываем общее количество продуктов
        cursor.execute("SELECT COUNT(*) FROM products")
        total_count = cursor.fetchone()[0]
        
        print(f"\nОбщее количество продуктов в базе данных: {total_count}")
        
        if total_count > 0:
            # Получаем информацию о первом и последнем продукте
            cursor.execute("""
                SELECT name, created_at 
                FROM products 
                ORDER BY created_at ASC 
                LIMIT 1
            """)
            first_product = cursor.fetchone()
            
            cursor.execute("""
                SELECT name, created_at 
                FROM products 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            last_product = cursor.fetchone()
            
            print("\nПервый добавленный продукт:")
            print(f"Название: {first_product[0]}")
            print(f"Добавлен: {first_product[1]}")
            
            print("\nПоследний добавленный продукт:")
            print(f"Название: {last_product[0]}")
            print(f"Добавлен: {last_product[1]}")
            
    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    count_products() 