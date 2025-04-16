import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

def check_duplicates():
    """Проверяет наличие дубликатов в базе данных"""
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
            # Проверяем дубликаты по URL
            query = """
            WITH duplicates AS (
                SELECT 
                    url,
                    COUNT(*) as count,
                    array_agg(id) as ids,
                    array_agg(name) as names,
                    array_agg(created_at) as created_dates
                FROM products
                GROUP BY url
                HAVING COUNT(*) > 1
            )
            SELECT 
                COUNT(DISTINCT url) as unique_urls_with_duplicates,
                SUM(count) as total_duplicate_records,
                SUM(count) - COUNT(DISTINCT url) as extra_records
            FROM duplicates;
            """
            
            cur.execute(query)
            result = cur.fetchone()
            
            if result:
                urls_with_dupes, total_dupes, extra_records = result
                if urls_with_dupes > 0:
                    print(f"Найдены дубликаты:")
                    print(f"- Количество URL с дубликатами: {urls_with_dupes}")
                    print(f"- Общее количество записей с дубликатами: {total_dupes}")
                    print(f"- Количество лишних записей: {extra_records}")
                    
                    # Показываем примеры дубликатов
                    query_examples = """
                    WITH duplicates AS (
                        SELECT 
                            url,
                            COUNT(*) as count,
                            array_agg(id ORDER BY id) as ids,
                            array_agg(name ORDER BY id) as names,
                            array_agg(created_at ORDER BY id) as created_dates
                        FROM products
                        GROUP BY url
                        HAVING COUNT(*) > 1
                        ORDER BY COUNT(*) DESC
                        LIMIT 5
                    )
                    SELECT url, count, ids, names, created_dates
                    FROM duplicates;
                    """
                    
                    cur.execute(query_examples)
                    examples = cur.fetchall()
                    
                    if examples:
                        print("\nПримеры дубликатов (первые 5):")
                        for url, count, ids, names, dates in examples:
                            print(f"\nURL: {url}")
                            print(f"Количество дубликатов: {count}")
                            print("Записи:")
                            for i in range(len(ids)):
                                print(f"- ID: {ids[i]}, Название: {names[i]}, Дата создания: {dates[i]}")
                else:
                    print("Дубликатов не найдено")
                
    except Exception as e:
        print(f"Ошибка при проверке дубликатов: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_duplicates() 