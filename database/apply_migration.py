import psycopg2
from pathlib import Path
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    """Применение миграции для добавления столбца subcategory"""
    try:
        # Загружаем переменные окружения
        load_dotenv()
        
        # Получаем параметры подключения
        db_params = {
            'dbname': os.getenv('DB_NAME', 'magic_products_db'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }
        
        # Подключаемся к PostgreSQL
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Читаем и выполняем миграционный SQL-скрипт
        logger.info('Applying migration...')
        migration_path = Path(__file__).parent / 'migrations' / 'add_subcategory.sql'
        with open(migration_path, 'r') as f:
            sql = f.read()
            cur.execute(sql)
        logger.info('Migration applied successfully')
        
        # Закрываем соединение
        cur.close()
        conn.close()
        logger.info('Database connection closed')
        
    except Exception as e:
        logger.error(f'Error applying migration: {e}')
        raise

if __name__ == '__main__':
    apply_migration() 