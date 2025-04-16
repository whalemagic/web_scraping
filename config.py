import os
from pathlib import Path

# Конфигурация для парсера Penguin Magic
config = {
    'base_url': 'https://www.penguinmagic.com/p/',
    'start_page': 7920,
    'end_page': 10000,
    'batch_size': 100,
    'max_retries': 3,
    'retry_delay': 5,
    'timeout': 30,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Конфигурация скрапера
SCRAPER_CONFIG = {
    'start_page': 7920,
    'end_page': 10000,
    'base_url': 'https://www.penguinmagic.com/p/',
    'data_dir': 'data',
    'log_dir': 'logs',
    'excel_file': 'data/products.xlsx',
    'excel_output': 'data/products.xlsx',
    'log_file': 'logs/scraper.log',
    'max_retries': 3,
    'retry_delay': 5,
    'timeout': 30,
    'batch_size': 100,
    'delay_between_requests': 1.0,
    'min_delay': 1.0,
    'max_delay': 3.0,
    'batch_delay': 30,
    'save_interval': 10,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
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