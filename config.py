# Настройки скрапера
SCRAPER_CONFIG = {
    'base_url': "https://www.penguinmagic.com/p",
    'start_page': 10001,
    'end_page': 11000,
    'min_delay': 1.0,  # минимальная задержка между запросами
    'max_delay': 2.5,  # максимальная задержка между запросами
    'output_file': "penguins10k-11k.xlsx",
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
    'max_retries': 3,  # максимальное количество попыток при ошибке
    'timeout': 30,  # таймаут запроса в секундах
    'batch_size': 50,  # количество запросов между паузами
    'batch_delay': 60  # пауза между батчами в секундах
}

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