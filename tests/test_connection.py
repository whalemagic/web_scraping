import psycopg2
from dotenv import load_dotenv
import os
from pathlib import Path

print("Загрузка переменных окружения...")
env_path = Path(__file__).parent / '.env'
print(f"Путь к файлу .env: {env_path}")
print(f"Файл существует: {env_path.exists()}")

if env_path.exists():
    print("\nСодержимое файла .env:")
    with open(env_path, 'r') as f:
        print(f.read())

load_dotenv(env_path, override=True)

print("\nЗначения переменных окружения:")
for var in ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']:
    value = os.getenv(var)
    if var == 'DB_PASSWORD':
        print(f"{var}: {'*' * len(value) if value else 'Не установлено'}")
    else:
        print(f"{var}: {value if value else 'Не установлено'}")

# Получаем и выводим параметры подключения
params = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

print("\nПараметры подключения:")
for key, value in params.items():
    if key == 'password':
        print(f"{key}: {'*' * len(value) if value else 'Не установлено'}")
    else:
        print(f"{key}: {value if value else 'Не установлено'}")

try:
    print("\nПытаемся подключиться к базе данных...")
    # Подключение к базе данных
    conn = psycopg2.connect(**params)
    print("\n✅ Подключение успешно!")
    
    # Создаем курсор
    cur = conn.cursor()
    
    # Выполняем простой запрос
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"\nВерсия PostgreSQL: {version[0]}")
    
    # Закрываем соединение
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Ошибка подключения: {str(e)}")
    print(f"Тип ошибки: {type(e).__name__}")
    
    if isinstance(e, psycopg2.OperationalError):
        print("\nДетали ошибки:")
        print(str(e).strip())
    
    # Выводим дополнительную информацию для отладки
    print("\nПроверьте следующее:")
    print("1. Правильность пароля в файле .env")
    print("2. Наличие прав у пользователя postgres")
    print("3. Настройки аутентификации в pg_hba.conf") 