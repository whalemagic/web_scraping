import psycopg2

print("Попытка подключения к базе данных...")

try:
    # Простое подключение с явными параметрами
    conn = psycopg2.connect(
        dbname="magic_products_db",
        user="postgres",
        password="Chesskit//4566",  # Замените на ваш пароль от pgAdmin
        host="localhost",
        port="5432"
    )
    print("✅ Подключение успешно!")
    
    # Проверяем версию PostgreSQL
    cur = conn.cursor()
    cur.execute('SELECT version()')
    version = cur.fetchone()
    print(f"Версия PostgreSQL: {version[0]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Ошибка подключения!")
    print(f"Тип ошибки: {type(e).__name__}")
    print(f"Описание: {str(e)}")
    print("\nПроверьте:")
    print("1. Правильность пароля")
    print("2. Что база данных запущена")
    print("3. Что PostgreSQL слушает порт 5432") 