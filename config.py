import os
from pathlib import Path

# Настройки скрапера
SCRAPER_CONFIG = {
    'base_url': 'https://www.penguinmagic.com',  # Базовый URL для скрапинга
    'start_page': 15001,  # Начальная страница
    'end_page': 15003,  # Конечная страница
    
    # Настройки запросов
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    },
    'timeout': 30,  # Таймаут запросов в секундах
    'max_retries': 3,  # Максимальное количество повторных попыток
    
    # Настройки задержек
    'min_delay': 2,  # Минимальная задержка между запросами в секундах
    'max_delay': 5,  # Максимальная задержка между запросами в секундах
    'batch_size': 5,  # Размер батча запросов
    'batch_delay': 60,  # Задержка между батчами в секундах
    
    # Настройки сохранения
    'save_interval': 10,  # Интервал сохранения (количество продуктов)
    'delay': 1.5,  # задержка между запросами в секундах
    'data_dir': 'data',  # директория для данных
    'excel_output': 'data/products.xlsx',  # путь к файлу Excel
    
    # Настройки логирования
    'log_dir': 'logs',  # директория для логов
    'log_file': 'logs/scraper.log',  # путь к файлу логов
}

# Создаем необходимые директории
for dir_path in [SCRAPER_CONFIG['data_dir'], SCRAPER_CONFIG['log_dir']]:
    os.makedirs(dir_path, exist_ok=True)

# Категории для классификации
CATEGORIES = {
    'card_magic': ['card', 'deck', 'playing cards', 'карты', 'колода'],
    'mentalism': ['mind reading', 'prediction', 'ментализм', 'предсказание'],
    'close_up': ['close-up', 'close up', 'клоуз-ап', 'фокусы вблизи'],
    'stage_magic': ['stage', 'platform', 'сцена', 'для сцены'],
    'coins': ['coin', 'монета', 'монеты'],
    'props': ['prop', 'реквизит', 'аксессуар'],
    'books': ['book', 'книга', 'обучение'],
    'downloads': ['download', 'instant', 'digital', 'цифровой продукт']
}

# Паттерны для поиска автора
AUTHOR_PATTERNS = [
    r'by\s+([^|]+)',  # "by Author Name"
    r'от\s+([^|]+)',  # "от Имя Автора"
    r'автор:\s*([^|]+)',  # "автор: Имя Автора"
    r'author:\s*([^|]+)',  # "author: Author Name"
    r'\|([^|]+)$',  # "Product Name | Author Name"
    r'-\s*([^|]+)$'  # "Product Name - Author Name"
] 