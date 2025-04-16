import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv

def check_last_page():
    """Проверяет последнюю обработанную страницу в диапазоне до 9000"""
    try:
        # Загружаем переменные окружения
        load_dotenv()
        
        # Подключаемся к базе данных
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        
        with conn.cursor() as cur:
            # Ищем максимальный номер страницы до 9000
            query = """
            SELECT MAX(CAST(SUBSTRING(url, 'p/(\d+)') AS INTEGER))
            FROM products
            WHERE url LIKE 'https://www.penguinmagic.com/p/%'
            AND CAST(SUBSTRING(url, 'p/(\d+)') AS INTEGER) < 9000
            """
            
            cur.execute(query)
            result = cur.fetchone()
            
            if result and result[0]:
                print(f"Последняя обработанная страница до 9000: {result[0]}")
            else:
                print("В базе нет записей для страниц до 9000")
                
    except Exception as e:
        print(f"Ошибка при проверке последней страницы: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_last_page() 