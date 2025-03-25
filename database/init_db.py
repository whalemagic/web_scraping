import psycopg2
from pathlib import Path
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Инициализация базы данных"""
    try:
        # Загружаем переменные окружения
        load_dotenv()
        
        # Получаем параметры подключения
        db_params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }
        
        # Подключаемся к PostgreSQL
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Проверяем версию PostgreSQL
        cur.execute('SELECT version();')
        version = cur.fetchone()
        logger.info(f'PostgreSQL version: {version[0]}')
        
        # Читаем и выполняем SQL-скрипт
        logger.info('Applying database schema...')
        with open(Path(__file__).parent / 'schema.sql', 'r') as f:
            sql = f.read()
            cur.execute(sql)
        logger.info('Database schema applied successfully')
        
        # Закрываем соединение
        cur.close()
        conn.close()
        logger.info('Database connection closed')
        
    except Exception as e:
        logger.error(f'Error initializing database: {e}')
        raise

if __name__ == '__main__':
    init_database() 