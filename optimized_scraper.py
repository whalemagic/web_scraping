import requests
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional
from config import SCRAPER_CONFIG, CATEGORIES, AUTHOR_PATTERNS
from database import save_to_database
import random
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class PenguinMagicScraper:
    def __init__(self):
        self.config = SCRAPER_CONFIG
        self.session = requests.Session()
        self.session.headers.update(self.config['headers'])
        self.products = []
        self.current_batch = 0

    def random_delay(self):
        """Случайная задержка между запросами"""
        delay = random.uniform(self.config['min_delay'], self.config['max_delay'])
        time.sleep(delay)

    def batch_delay(self):
        """Пауза между батчами запросов"""
        if self.current_batch >= self.config['batch_size']:
            logging.info(f"Достигнут лимит батча ({self.config['batch_size']} запросов). Пауза {self.config['batch_delay']} секунд.")
            time.sleep(self.config['batch_delay'])
            self.current_batch = 0

    def make_request(self, url: str, retry_count: int = 0) -> Optional[requests.Response]:
        """Выполнение запроса с обработкой ошибок и повторными попытками"""
        try:
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if retry_count < self.config['max_retries']:
                logging.warning(f"Ошибка запроса: {e}. Повторная попытка {retry_count + 1}/{self.config['max_retries']}")
                time.sleep(random.uniform(2, 5))  # Увеличенная задержка при ошибке
                return self.make_request(url, retry_count + 1)
            else:
                logging.error(f"Превышено максимальное количество попыток для URL: {url}")
                return None

    def scrape_page(self, page_number: int) -> List[Dict]:
        """Скрапинг одной страницы"""
        url = f"{self.config['base_url']}/{page_number}"
        logging.info(f"Обработка страницы {page_number}")
        
        response = self.make_request(url)
        if not response:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        
        # Ваш существующий код парсинга страницы
        # ...

        self.current_batch += 1
        self.batch_delay()
        return products

    def run(self):
        """Запуск скрапера"""
        start_time = datetime.now()
        logging.info(f"Начало скрапинга: {start_time}")

        for page in range(self.config['start_page'], self.config['end_page'] + 1):
            try:
                products = self.scrape_page(page)
                self.products.extend(products)
                
                # Сохранение промежуточных результатов каждые 100 страниц
                if len(self.products) % 100 == 0:
                    self.save_results()
                    logging.info(f"Сохранено {len(self.products)} продуктов")
                
                self.random_delay()
                
            except Exception as e:
                logging.error(f"Ошибка при обработке страницы {page}: {e}")
                continue

        self.save_results()
        end_time = datetime.now()
        duration = end_time - start_time
        logging.info(f"Скрапинг завершен. Длительность: {duration}")

    def save_results(self):
        """Сохранение результатов в Excel"""
        df = pd.DataFrame(self.products)
        df.to_excel(self.config['output_file'], index=False)
        logging.info(f"Результаты сохранены в {self.config['output_file']}")

def main():
    try:
        scraper = PenguinMagicScraper()
        logging.info("Начало работы скрапера")
        
        scraper.run()
        
        # Сохранение в базу данных
        save_to_database(scraper.products)
        
        logging.info("Работа скрапера завершена успешно")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main() 