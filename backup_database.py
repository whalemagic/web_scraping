import os
from dotenv import load_dotenv
from datetime import datetime
import subprocess

def backup_database():
    try:
        # Загружаем параметры подключения из .env
        load_dotenv()
        
        # Создаем директорию для бэкапов, если её нет
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Создаем имя файла с текущей датой и временем
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"penguin_magic_backup_{timestamp}.sql")
        
        # Формируем команду для создания бэкапа
        cmd = [
            "pg_dump",
            "-h", os.getenv('DB_HOST'),
            "-p", os.getenv('DB_PORT'),
            "-U", os.getenv('DB_USER'),
            "-d", os.getenv('DB_NAME'),
            "-F", "c",  # Формат custom
            "-f", backup_file
        ]
        
        # Устанавливаем переменную окружения с паролем
        env = os.environ.copy()
        env["PGPASSWORD"] = os.getenv('DB_PASSWORD')
        
        # Выполняем команду
        subprocess.run(cmd, env=env, check=True)
        
        print(f"\nРезервная копия успешно создана: {backup_file}")
        
        # Проверяем размер файла
        file_size = os.path.getsize(backup_file) / (1024 * 1024)  # Размер в МБ
        print(f"Размер файла: {file_size:.2f} МБ")
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании резервной копии: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    backup_database() 