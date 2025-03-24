import os
from pathlib import Path

# Настройки скрапера
SCRAPER_CONFIG = {
    'base_url': 'https://www.penguinmagic.com',  # Базовый URL для скрапинга
    'start_page': 15001,  # Начальная страница
    'end_page': 15100,  # Конечная страница
    
    # Настройки запросов
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
    'timeout': 30,  # Таймаут запросов в секундах
    'max_retries': 3,  # Максимальное количество повторных попыток
    
    # Настройки задержек
    'min_delay': 2,  # Минимальная задержка между запросами в секундах
    'max_delay': 5,  # Максимальная задержка между запросами в секундах
    'batch_size': 5,  # Размер батча запросов
    'batch_delay': 60,  # Задержка между батчами в секундах
    
    # Настройки сохранения
    'save_interval': 20,  # Интервал сохранения (количество продуктов)
    'excel_output': 'products.xlsx',  # Путь к файлу Excel
    
    # Настройки логирования
    'log_file': 'scraper.log',  # Путь к файлу логов
    'log_level': 'INFO',  # Уровень логирования
}

# Создаем директорию для выходных файлов, если она не существует
output_dir = Path('output')
output_dir.mkdir(exist_ok=True)

# Обновляем пути с учетом директории output
SCRAPER_CONFIG['excel_output'] = str(output_dir / SCRAPER_CONFIG['excel_output'])
SCRAPER_CONFIG['log_file'] = str(output_dir / SCRAPER_CONFIG['log_file'])

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