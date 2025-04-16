import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

def export_to_excel():
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
        
        # Получаем все данные из таблицы products
        cursor.execute("""
            SELECT 
                id,
                name,
                author,
                price,
                url,
                image_url,
                description,
                categories,
                created_at,
                updated_at
            FROM products
            ORDER BY id
        """)
        
        # Получаем все записи
        products = cursor.fetchall()
        
        # Создаем DataFrame
        df = pd.DataFrame(products)
        
        # Создаем имя файла с текущей датой и временем
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"products_export_{timestamp}.xlsx"
        
        # Сохраняем в Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\nДанные успешно экспортированы в файл: {filename}")
        print(f"Всего экспортировано записей: {len(df)}")
        
    except Exception as e:
        print(f"Ошибка при экспорте данных: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    export_to_excel() 