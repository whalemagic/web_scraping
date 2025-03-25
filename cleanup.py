import os
import shutil
from config import SCRAPER_CONFIG
from database.db_manager import DatabaseManager

def cleanup_old_files():
    """Очистка файлов и директорий перед запуском скрапера"""
    # Очистка базы данных
    print("Очистка базы данных...")
    with DatabaseManager() as db:
        db.cur.execute("DELETE FROM products")
        db.conn.commit()
    print("База данных очищена")
    
    # Очистка Excel файла
    excel_path = os.path.join('data', 'products.xlsx')
    if os.path.exists(excel_path):
        os.remove(excel_path)
        print(f"Excel файл удален: {excel_path}")
    
    # Очистка кэша Python
    dirs_to_clean = [
        '__pycache__',
        'tests/__pycache__',
        'database/__pycache__'
    ]
    
    # Удаляем директории с кэшем
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"Удалена директория: {dir_path}")
            except Exception as e:
                print(f"Ошибка при удалении директории {dir_path}: {e}")
    
    # Создаем директории для данных и логов
    os.makedirs(SCRAPER_CONFIG['data_dir'], exist_ok=True)
    os.makedirs(SCRAPER_CONFIG['log_dir'], exist_ok=True)
    print(f"Созданы директории для данных и логов")

if __name__ == "__main__":
    cleanup_old_files() 