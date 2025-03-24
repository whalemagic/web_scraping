import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import os

def init_database():
    # Загружаем переменные окружения
    env_path = Path(__file__).parent.parent / '.env'
    print(f"Путь к файлу .env: {env_path}")
    print(f"Файл существует: {env_path.exists()}")
    
    load_dotenv(env_path, override=True)

    # Параметры подключения
    params = {
        'dbname': 'postgres',  # Сначала подключаемся к базе postgres
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }

    print("\nПараметры подключения:")
    for key, value in params.items():
        if key == 'password':
            print(f"{key}: {'*' * len(str(value)) if value else 'Не установлено'}")
        else:
            print(f"{key}: {value if value else 'Не установлено'}")

    try:
        # Подключаемся к PostgreSQL
        print("\nПодключаемся к базе данных postgres...")
        conn = psycopg2.connect(**params)
        conn.autocommit = True  # Включаем автокоммит для создания базы данных
        cur = conn.cursor()

        # Создаем базу данных
        print("\nПроверяем существование базы данных magic_products_db...")
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'magic_products_db'")
        exists = cur.fetchone()
        if not exists:
            print("Создаем базу данных magic_products_db...")
            cur.execute('CREATE DATABASE magic_products_db')
            print("База данных успешно создана!")
        else:
            print("База данных уже существует.")

        # Закрываем соединение
        cur.close()
        conn.close()

        # Подключаемся к новой базе данных
        print("\nПодключаемся к базе данных magic_products_db...")
        params['dbname'] = 'magic_products_db'
        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        # Читаем и выполняем SQL-скрипт
        print("\nСоздаем таблицы и индексы...")
        with open(Path(__file__).parent / 'init.sql', 'r') as f:
            sql = f.read()
            cur.execute(sql)

        conn.commit()
        print("Структура базы данных успешно создана!")

        # Проверяем создание таблицы
        cur.execute("SELECT COUNT(*) FROM products")
        count = cur.fetchone()[0]
        print(f"\nТаблица products создана. Количество записей: {count}")

    except Exception as e:
        print(f"\n❌ Ошибка при инициализации базы данных: {str(e)}")
        print(f"Тип ошибки: {type(e).__name__}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    print("Начинаем инициализацию базы данных...")
    init_database()
    print("\nИнициализация завершена!") 