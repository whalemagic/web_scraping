import os
from pathlib import Path
import psycopg2
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
    cur = conn.cursor()
    
    # Проверяем существующие таблицы
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    
    tables = cur.fetchall()
    
    print("\nСуществующие таблицы в базе данных:")
    print("-" * 40)
    for table in tables:
        # Получаем структуру таблицы
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table[0]}'
        """)
        columns = cur.fetchall()
        
        print(f"\nТаблица: {table[0]}")
        print("Колонки:")
        for column in columns:
            print(f"  - {column[0]}: {column[1]}")
    
except Exception as e:
    print(f"\nОшибка при работе с базой данных: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close() 