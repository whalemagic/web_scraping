import os
import shutil
import pandas as pd
import logging
from config import SCRAPER_CONFIG
from database.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_files():
    """Очистка файлов и директорий перед запуском скрапера"""
    try:
        # Очистка базы данных
        print("Очистка базы данных...")
        with DatabaseManager() as db:
            db.execute_query("DELETE FROM products")
            db.conn.commit()
        print("База данных очищена")
        
        # Очистка Excel файла
        excel_path = os.path.join('data', 'products.xlsx')
        if os.path.exists(excel_path):
            os.remove(excel_path)
            print(f"Excel файл удален: {excel_path}")
        
        # Создаем директории для данных и логов
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        print(f"Созданы директории для данных и логов")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке файлов: {e}")

def cleanup_excel():
    """Очистка Excel файла с результатами"""
    try:
        excel_path = os.path.join('data', 'products.xlsx')
        
        # Создаем пустой DataFrame с теми же колонками
        empty_df = pd.DataFrame(columns=[
            'name', 'author', 'price', 'url', 
            'image_url', 'description', 'categories'
        ])
        
        # Сохраняем пустой DataFrame в Excel
        empty_df.to_excel(excel_path, index=False)
        logger.info(f"Файл {excel_path} успешно очищен")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке Excel файла: {e}")

if __name__ == "__main__":
    cleanup_old_files()
    cleanup_excel() 