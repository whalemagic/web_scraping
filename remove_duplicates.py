import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

def remove_duplicates():
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
        
        with conn.cursor() as cur:
            # Создаем временную таблицу с уникальными записями
            cur.execute("""
                CREATE TEMP TABLE temp_products AS
                SELECT DISTINCT ON (url) *
                FROM products
                ORDER BY url, created_at DESC;
            """)
            
            # Удаляем все записи из основной таблицы
            cur.execute("TRUNCATE TABLE products RESTART IDENTITY;")
            
            # Вставляем уникальные записи обратно
            cur.execute("""
                INSERT INTO products
                SELECT * FROM temp_products;
            """)
            
            # Удаляем временную таблицу
            cur.execute("DROP TABLE temp_products;")
            
            # Подсчитываем оставшиеся записи
            cur.execute("SELECT COUNT(*) FROM products;")
            count = cur.fetchone()[0]
            
            conn.commit()
            print(f"\nУдаление дубликатов завершено. Осталось {count} уникальных записей.")
            
    except Exception as e:
        print(f"Ошибка при удалении дубликатов: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    remove_duplicates() 