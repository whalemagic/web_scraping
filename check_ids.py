import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv

def check_ids():
    load_dotenv()
    
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Получаем минимальный и максимальный ID
            cur.execute("""
                SELECT 
                    MIN(id) as min_id,
                    MAX(id) as max_id,
                    COUNT(*) as total_count
                FROM products
            """)
            result = cur.fetchone()
            print(f"\nДиапазон ID: от {result['min_id']} до {result['max_id']}")
            print(f"Всего записей: {result['total_count']}")
            
            # Получаем даты первой и последней записи
            cur.execute("""
                SELECT 
                    MIN(created_at) as first_date,
                    MAX(created_at) as last_date
                FROM products
            """)
            dates = cur.fetchone()
            print(f"\nПервая запись создана: {dates['first_date']}")
            print(f"Последняя запись создана: {dates['last_date']}")
            
            # Проверяем дубликаты по URL
            cur.execute("""
                SELECT url, COUNT(*) as count
                FROM products
                GROUP BY url
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 5
            """)
            duplicates = cur.fetchall()
            if duplicates:
                print("\nНайдены дубликаты по URL:")
                for dup in duplicates:
                    print(f"URL: {dup['url']} - {dup['count']} раз")
            else:
                print("\nДубликатов по URL не найдено")
                
    except Exception as e:
        print(f"Ошибка при проверке ID: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_ids() 