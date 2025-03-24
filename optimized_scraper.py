import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional
from config import SCRAPER_CONFIG
from database.db_manager import DatabaseManager
import random
import sys
from urllib.parse import urljoin
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PenguinMagicScraper:
    def __init__(self):
        """Инициализация скрапера"""
        self.config = SCRAPER_CONFIG
        self.session = requests.Session()
        self.session.headers.update(self.config['headers'])
        self.products = []
        self.current_batch = 0
        self.db_manager = DatabaseManager()

    def random_delay(self):
        """Случайная задержка между запросами"""
        delay = random.uniform(self.config['min_delay'], self.config['max_delay'])
        time.sleep(delay)

    def batch_delay(self):
        """Пауза между батчами запросов"""
        if self.current_batch >= self.config['batch_size']:
            logger.info(f"Достигнут лимит батча ({self.config['batch_size']} запросов). Пауза {self.config['batch_delay']} секунд.")
            time.sleep(self.config['batch_delay'])
            self.current_batch = 0

    def make_request(self, url: str, retry_count: int = 0) -> Optional[requests.Response]:
        """Выполнение запроса с обработкой ошибок и повторными попытками"""
        try:
            response = self.session.get(url, timeout=self.config['timeout'])
            
            # Специальная обработка 500 ошибки
            if response.status_code == 500:
                logger.warning(f"Страница {url} вернула 500 ошибку (возможно удалена)")
                return None
                
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            if retry_count < self.config['max_retries']:
                logger.warning(f"Ошибка запроса: {e}. Повторная попытка {retry_count + 1}/{self.config['max_retries']}")
                time.sleep(random.uniform(2, 5))  # Увеличенная задержка при ошибке
                return self.make_request(url, retry_count + 1)
            else:
                logger.error(f"Превышено максимальное количество попыток для URL: {url}")
                return None

    def extract_product_info(self, product_element) -> Optional[Dict]:
        """Извлечение информации о продукте из HTML элемента"""
        try:
            # Название продукта
            name_element = product_element.find('div', class_='text')
            if not name_element:
                return None

            product_name = name_element.text.strip()
            
            # URL продукта
            link_element = product_element.find('a')
            if not link_element:
                return None
                
            product_url = link_element.get('href')
            if not product_url.startswith('http'):
                product_url = urljoin(self.config['base_url'], product_url)

            # Изображение
            img_element = product_element.find('img')
            image_url = img_element.get('src') if img_element else None

            # Цена (получаем из детальной страницы)
            product_details = self.get_product_details(product_url)
            if not product_details:
                return None

            product_info = {
                'name': product_name,
                'price': product_details.get('price'),
                'url': product_url,
                'image_url': image_url or product_details.get('image_url'),
                'description': product_details.get('description'),
                'category': product_details.get('category'),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            logger.info(f"Извлечена информация о продукте: {product_name}")
            return product_info

        except Exception as e:
            logger.error(f"Ошибка при извлечении информации о продукте: {e}")
            return None

    def get_product_details(self, product_url: str) -> Optional[Dict]:
        """Получение детальной информации о продукте"""
        try:
            response = self.make_request(product_url)
            if not response:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Цена
            price_element = soup.find(['span', 'div', 'p'], string=lambda text: text and '$' in text)
            price = None
            if price_element:
                price_text = price_element.text.strip()
                # Извлекаем число из строки с ценой (например, из "$19.95")
                price_match = re.search(r'\$?(\d+\.?\d*)', price_text)
                if price_match:
                    price = float(price_match.group(1))
            
            # Описание
            description_element = soup.find('div', class_='product_description')
            description = description_element.text.strip() if description_element else None
            
            # Категория
            breadcrumbs = soup.find('div', class_='breadcrumbs')
            category = None
            if breadcrumbs:
                category_link = breadcrumbs.find_all('a')[-1]
                category = category_link.text.strip() if category_link else None

            return {
                'price': price,
                'description': description,
                'category': category
            }

        except Exception as e:
            logger.error(f"Ошибка при получении деталей продукта {product_url}: {e}")
            return None

    def scrape_page(self, page_number: int) -> List[Dict]:
        """Скрапинг одной страницы"""
        url = f"{self.config['base_url']}/{page_number}"
        logger.info(f"Обработка страницы {page_number}")
        
        response = self.make_request(url)
        if not response:
            logger.info(f"Страница {page_number} пропущена (недоступна)")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        products_elements = soup.find_all('div', class_='tt_box')
        
        if not products_elements:
            logger.info(f"На странице {page_number} не найдено продуктов")
            return []
            
        products = []
        for product_element in products_elements:
            product_info = self.extract_product_info(product_element)
            if product_info:
                products.append(product_info)
                logger.debug(f"Добавлен продукт: {product_info['name']}")

        self.current_batch += 1
        self.batch_delay()
        
        logger.info(f"Со страницы {page_number} получено {len(products)} продуктов")
        return products

    def save_to_excel(self, filename: str):
        """Сохранение результатов в Excel"""
        try:
            df = pd.DataFrame(self.products)
            df.to_excel(filename, index=False)
            logger.info(f"Данные успешно сохранены в Excel: {filename}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в Excel: {e}")

    def save_to_database(self):
        """Сохранение результатов в базу данных"""
        try:
            with self.db_manager as db:
                for product in self.products:
                    try:
                        db.add_product(product)
                        logger.info(f"Продукт '{product['name']}' успешно сохранен в базу данных")
                    except Exception as e:
                        logger.error(f"Ошибка при сохранении продукта '{product['name']}' в базу данных: {e}")
        except Exception as e:
            logger.error(f"Ошибка при работе с базой данных: {e}")

    def run(self):
        """Запуск скрапера"""
        start_time = datetime.now()
        logger.info(f"Начало скрапинга: {start_time}")

        try:
            for page in range(self.config['start_page'], self.config['end_page'] + 1):
                try:
                    products = self.scrape_page(page)
                    self.products.extend(products)
                    
                    # Сохранение промежуточных результатов
                    if len(self.products) % self.config['save_interval'] == 0:
                        self.save_to_excel(self.config['excel_output'])
                        self.save_to_database()
                        logger.info(f"Сохранено {len(self.products)} продуктов")
                    
                    self.random_delay()
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке страницы {page}: {e}")
                    continue

            # Финальное сохранение
            self.save_to_excel(self.config['excel_output'])
            self.save_to_database()

        except Exception as e:
            logger.error(f"Критическая ошибка при работе скрапера: {e}")
        finally:
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Скрапинг завершен. Длительность: {duration}")

def main():
    try:
        scraper = PenguinMagicScraper()
        logger.info("Начало работы скрапера")
        scraper.run()
        logger.info("Работа скрапера завершена успешно")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main() 