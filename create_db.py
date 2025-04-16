import sqlite3
from datetime import datetime

def create_database():
    try:
        # Подключаемся к базе данных (создастся, если не существует)
        conn = sqlite3.connect('products.db')
        cursor = conn.cursor()
        
        # Создаем таблицу products, если она не существует
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                price REAL,
                description TEXT,
                categories TEXT,
                author TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("База данных успешно инициализирована!")
        
    except sqlite3.Error as e:
        print(f"Ошибка при создании базы данных: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database() 