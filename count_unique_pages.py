import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

def count_unique_pages():
    """Подсчитывает количество уникальных страниц в базе данных"""
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
            # Считаем уникальные страницы
            query = """
            WITH page_numbers AS (
                SELECT DISTINCT CAST(SUBSTRING(url, 'p/(\d+)') AS INTEGER) as page_number
                FROM products
                WHERE url LIKE 'https://www.penguinmagic.com/p/%'
            )
            SELECT 
                COUNT(*) as total_pages,
                MIN(page_number) as min_page,
                MAX(page_number) as max_page
            FROM page_numbers
            """
            
            cur.execute(query)
            result = cur.fetchone()
            
            if result:
                total_pages, min_page, max_page = result
                print(f"Всего уникальных страниц в базе: {total_pages}")
                print(f"Диапазон страниц: от {min_page} до {max_page}")
                
                # Дополнительно проверим пропущенные страницы
                query_gaps = """
                WITH RECURSIVE 
                numbers AS (
                    SELECT MIN(CAST(SUBSTRING(url, 'p/(\d+)') AS INTEGER)) as num 
                    FROM products 
                    WHERE url LIKE 'https://www.penguinmagic.com/p/%'
                    UNION ALL
                    SELECT num + 1 
                    FROM numbers 
                    WHERE num < (
                        SELECT MAX(CAST(SUBSTRING(url, 'p/(\d+)') AS INTEGER)) 
                        FROM products 
                        WHERE url LIKE 'https://www.penguinmagic.com/p/%'
                    )
                ),
                existing_pages AS (
                    SELECT DISTINCT CAST(SUBSTRING(url, 'p/(\d+)') AS INTEGER) as page_number
                    FROM products
                    WHERE url LIKE 'https://www.penguinmagic.com/p/%'
                )
                SELECT n.num as missing_page
                FROM numbers n
                LEFT JOIN existing_pages e ON n.num = e.page_number
                WHERE e.page_number IS NULL
                ORDER BY n.num
                LIMIT 5
                """
                
                cur.execute(query_gaps)
                gaps = cur.fetchall()
                if gaps:
                    print("\nПримеры пропущенных страниц (первые 5):")
                    for gap in gaps:
                        print(f"- Страница {gap[0]}")
                
    except Exception as e:
        print(f"Ошибка при подсчете страниц: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    count_unique_pages() 