import os
import shutil
from pathlib import Path
from config import SCRAPER_CONFIG

def cleanup_old_files():
    """Очищает старые файлы и создает необходимые директории"""
    # Создаем необходимые директории
    for dir_path in [SCRAPER_CONFIG['data_dir'], SCRAPER_CONFIG['log_dir']]:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Создана директория: {dir_path}")

if __name__ == "__main__":
    cleanup_old_files() 