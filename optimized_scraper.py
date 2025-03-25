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
import os

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
        self.current_url = None
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
            self.current_url = url
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
            # Название продукта и автор
            title_element = product_element.find('title')
            if not title_element:
                logger.warning("Не найден заголовок продукта")
                return None

            product_name = title_element.text.strip()
            
            # Извлекаем автора из названия
            author = None
            author_match = re.search(r'by\s+([^(]+?)(?:\s*\(|$)', product_name)
            if author_match:
                author = author_match.group(1).strip()
            
            # URL продукта - берем из текущего URL
            product_url = self.current_url
            
            # Изображение
            meta_image = product_element.find('meta', {'property': 'og:image'})
            image_url = None
            if meta_image:
                image_url = meta_image.get('content')
            
            # Цена - ищем в мета-тегах и в тексте страницы
            price = None
            # Сначала ищем в мета-тегах
            meta_price = product_element.find('meta', {'property': 'product:price:amount'})
            if meta_price:
                try:
                    price = float(meta_price.get('content'))
                except (ValueError, TypeError):
                    pass
            
            # Если не нашли в мета-тегах, ищем в заголовке
            if not price:
                price_match = re.search(r'\$(\d+\.?\d*)', product_name)
                if price_match:
                    try:
                        price = float(price_match.group(1))
                    except ValueError:
                        pass
            
            # Если все еще не нашли, устанавливаем значение по умолчанию
            if not price:
                price = 9.95  # Большинство продуктов на сайте стоят $9.95
            
            # Описание
            description_meta = product_element.find('meta', {'property': 'og:description'})
            description = description_meta.get('content').strip() if description_meta else None
            
            # Категория
            category = None
            keywords_meta = product_element.find('meta', {'name': 'keywords'})
            if keywords_meta:
                keywords = keywords_meta.get('content', '').split(',')
                if keywords:
                    category = keywords[0].strip()

            product_info = {
                'name': product_name,
                'author': author,
                'price': price,
                'url': product_url,
                'image_url': image_url,
                'description': description,
                'category': category,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            logger.info(f"Извлечена информация о продукте: {product_name} (${price})")
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
            
            # Используем основной метод извлечения информации
            product_container = soup.find('div', class_='product-main')
            if not product_container:
                logger.warning(f"Не найден контейнер продукта на странице {product_url}")
                return None
                
            return self.extract_product_info(product_container)

        except Exception as e:
            logger.error(f"Ошибка при получении деталей продукта {product_url}: {e}")
            return None

    def scrape_page(self, page_number: int) -> Optional[Dict]:
        """Скрапинг одной страницы"""
        url = f"{self.config['base_url']}/p/{page_number}"
        logger.info(f"Обработка страницы {page_number}")
        
        response = self.make_request(url)
        if not response:
            logger.info(f"Страница {page_number} пропущена (недоступна)")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Проверяем наличие основного контейнера продукта
        head = soup.find('head')
        if not head:
            logger.info(f"На странице {page_number} не найден head")
            return None
            
        # Извлекаем информацию о продукте
        product_info = self.extract_product_info(head)
        if product_info:
            logger.info(f"Получена информация о продукте со страницы {page_number}")
            return product_info
        
        logger.info(f"Не удалось извлечь информацию о продукте со страницы {page_number}")
        return None

    def save_to_excel(self, filename: str):
        """Сохранение результатов в Excel"""
        try:
            # Создаем директорию для файла, если она не существует
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Преобразуем данные в DataFrame
            df = pd.DataFrame(self.products)
            
            # Сохраняем с указанием всех столбцов
            columns = ['name', 'author', 'price', 'url', 'image_url', 'description', 'category', 'created_at', 'updated_at']
            df = df.reindex(columns=columns)
            
            # Сохраняем файл
            df.to_excel(filename, index=False)
            logger.info(f"Данные успешно сохранены в Excel: {filename} (сохранено {len(df)} продуктов)")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в Excel: {e}")
            raise

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
                    product_info = self.scrape_page(page)
                    if product_info:
                        self.products.append(product_info)
                        
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