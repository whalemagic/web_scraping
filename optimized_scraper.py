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
import json

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
        self.logger = logging.getLogger(__name__)

    def random_delay(self):
        """Случайная задержка между запросами"""
        delay = random.uniform(self.config['min_delay'], self.config['max_delay'])
        time.sleep(delay)

    def batch_delay(self):
        """Пауза между батчами запросов"""
        if self.current_batch >= self.config['batch_size']:
            self.logger.info(f"Достигнут лимит батча ({self.config['batch_size']} запросов). Пауза {self.config['batch_delay']} секунд.")
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

    def extract_product_info(self, soup, url):
        """Извлекает информацию о продукте из HTML"""
        try:
            # Название продукта
            product_name = None
            
            # 1. Ищем в основном контейнере продукта
            product_container = soup.find('div', class_='product-main')
            if product_container:
                # Ищем заголовок в контейнере
                title_element = product_container.find('h1')
                if title_element:
                    product_name = title_element.text.strip()
            
            # 2. Ищем в мета-тегах
            if not product_name:
                meta_title = soup.find('meta', {'property': 'og:title'})
                if meta_title:
                    product_name = meta_title.get('content', '').strip()
                    # Удаляем лишние части из заголовка
                    product_name = product_name.replace(' - Penguin Magic Shop', '').strip()
            
            # 3. Ищем в заголовке страницы
            if not product_name:
                title_element = soup.find('title')
                if title_element:
                    product_name = title_element.text.strip()
                    # Удаляем лишние части из заголовка
                    product_name = product_name.replace(' - Penguin Magic Shop', '').strip()
            
            if not product_name:
                product_name = "Название не найдено"
            
            # Извлекаем автора из названия
            author = None
            author_match = re.search(r'by\s+([^(]+?)(?:\s*\(|$)', product_name)
            if author_match:
                author = author_match.group(1).strip()
            
            # Цена - ищем во всех возможных местах
            price = None
            
            # 1. Ищем в таблице с ценой
            price_table = soup.find('table', class_='price-table')
            if price_table:
                price_cell = price_table.find('td', class_='price')
                if price_cell:
                    try:
                        price_text = price_cell.text.strip()
                        price = float(price_text.replace('$', ''))
                    except (ValueError, TypeError):
                        pass
            
            # 2. Ищем в JSON-данных
            if not price:
                script_tags = soup.find_all('script', {'type': 'application/ld+json'})
                for script in script_tags:
                    try:
                        json_data = json.loads(script.string)
                        if isinstance(json_data, dict):
                            if 'offers' in json_data:
                                offers = json_data['offers']
                                if isinstance(offers, dict) and 'price' in offers:
                                    price = float(offers['price'])
                                    break
                    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
                        continue
            
            # 3. Ищем в мета-тегах
            if not price:
                meta_price = soup.find('meta', {'property': 'product:price:amount'})
                if meta_price:
                    try:
                        price = float(meta_price.get('content'))
                    except (ValueError, TypeError):
                        pass
            
            # 4. Ищем в элементах с ценой
            if not price:
                price_selectors = [
                    ('span', {'class': 'price'}),
                    ('div', {'class': 'product-price'}),
                    ('span', {'class': 'regular-price'}),
                    ('div', {'class': 'price-box'}),
                    ('span', {'itemprop': 'price'})
                ]
                
                for tag, attrs in price_selectors:
                    price_element = soup.find(tag, attrs)
                    if price_element:
                        try:
                            price_text = price_element.text.strip()
                            # Удаляем все нечисловые символы, кроме точки
                            price_text = ''.join(filter(lambda x: x.isdigit() or x == '.', price_text))
                            if price_text:
                                price = float(price_text)
                                break
                        except (ValueError, TypeError):
                            continue
            
            # 5. Ищем цену в тексте страницы с помощью регулярных выражений
            if not price:
                price_patterns = [
                    r'\$(\d+\.?\d*)',
                    r'Price:\s*\$(\d+\.?\d*)',
                    r'price:\s*\$(\d+\.?\d*)'
                ]
                
                for pattern in price_patterns:
                    price_matches = re.findall(pattern, str(soup))
                    if price_matches:
                        try:
                            # Берем максимальную цену из найденных (обычно это реальная цена)
                            price = max(float(p) for p in price_matches)
                            break
                        except (ValueError, TypeError):
                            continue
            
            # Если цена все еще не найдена, логируем это
            if not price:
                logger.warning(f"Не удалось найти цену для продукта {url}")
                price = 0.0
            
            # URL изображения
            image_url = None
            meta_image = soup.find('meta', {'property': 'og:image'})
            if meta_image:
                image_url = meta_image.get('content')
            
            # Описание
            description = None
            description_meta = soup.find('meta', {'property': 'og:description'})
            if description_meta:
                description = description_meta.get('content').strip()
            
            # Категории
            categories = []
            keywords_meta = soup.find('meta', {'name': 'keywords'})
            if keywords_meta:
                categories = [k.strip() for k in keywords_meta.get('content', '').split(',')]
            
            product_info = {
                'name': product_name,
                'author': author,
                'price': price,
                'url': url,
                'image_url': image_url,
                'description': description,
                'categories': categories,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            logger.info(f"Извлечена информация о продукте: {product_name} (${price})")
            return product_info
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации о продукте {url}: {str(e)}")
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
                
            return self.extract_product_info(soup, product_url)

        except Exception as e:
            logger.error(f"Ошибка при получении деталей продукта {product_url}: {e}")
            return None

    def scrape_page(self, page_number: int) -> Optional[Dict]:
        """Скрапинг одной страницы"""
        url = self.get_product_url(page_number)
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
        product_info = self.extract_product_info(soup, url)
        if product_info:
            logger.info(f"Получена информация о продукте со страницы {page_number}")
            return product_info
        
        logger.info(f"Не удалось извлечь информацию о продукте со страницы {page_number}")
        return None

    def get_product_url(self, page_number):
        """Формирует URL для страницы продукта"""
        return f"{self.config['base_url']}{page_number}"

    def save_to_excel(self, filename: str):
        """Сохранение результатов в Excel с добавлением к существующим данным"""
        try:
            # Создаем директорию для файла, если она не существует
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Преобразуем новые данные в DataFrame
            new_df = pd.DataFrame(self.products)
            
            # Определяем столбцы
            columns = ['name', 'author', 'price', 'url', 'image_url', 'description', 'categories']
            new_df = new_df.reindex(columns=columns)
            
            # Очищаем текст от специальных символов
            def clean_text(text):
                if pd.isna(text):
                    return text
                # Преобразуем в строку
                text = str(text)
                # Удаляем переносы строк и табуляции
                text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                # Удаляем специальные символы Excel
                text = ''.join(char for char in text if ord(char) < 65536)
                # Удаляем лишние пробелы
                text = ' '.join(text.split())
                return text
            
            # Применяем очистку к текстовым полям
            for col in ['name', 'author', 'description']:
                if col in new_df.columns:
                    new_df[col] = new_df[col].apply(clean_text)
            
            # Пытаемся прочитать существующий файл
            try:
                if os.path.exists(filename):
                    existing_df = pd.read_excel(filename)
                    # Проверяем и добавляем недостающие столбцы
                    for col in columns:
                        if col not in existing_df.columns:
                            existing_df[col] = None
                    # Оставляем только нужные столбцы в правильном порядке
                    existing_df = existing_df.reindex(columns=columns)
                    
                    # Объединяем существующие и новые данные
                    # Используем url как ключ для удаления дубликатов
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=['url'], keep='last')
                else:
                    combined_df = new_df
            except Exception as e:
                logger.warning(f"Не удалось прочитать существующий файл {filename}: {e}")
                combined_df = new_df
            
            # Сохраняем объединенный результат
            combined_df.to_excel(filename, index=False)
            logger.info(f"Данные успешно сохранены в Excel: {filename} (всего {len(combined_df)} продуктов)")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении в Excel: {e}")
            raise

    def save_to_database(self, products):
        """Сохраняет продукты в базу данных"""
        try:
            # Сохраняем только последний батч
            if not products:
                return
            
            # Подключаемся к базе данных
            self.db_manager.connect()
            
            # Сохраняем каждый продукт
            for product in products:
                try:
                    self.db_manager.save_product(product)
                    self.logger.info(f"Продукт '{product['name']}' успешно сохранен в базу данных")
                except Exception as e:
                    self.logger.error(f"Ошибка при сохранении продукта {product['name']}: {e}")
            
            # Закрываем соединение
            if self.db_manager.conn:
                self.db_manager.conn.close()
                self.db_manager.cur = None
                self.db_manager.conn = None
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении в базу данных: {e}")
            if self.db_manager.conn:
                self.db_manager.conn.close()
                self.db_manager.cur = None
                self.db_manager.conn = None

    def run(self):
        """Запуск скрапера"""
        try:
            logger.info("Начало работы скрапера")
            
            # Создаем прогресс-бар
            total_pages = self.config['end_page'] - self.config['start_page'] + 1
            with tqdm(total=total_pages, desc="Обработка страниц") as pbar:
                # Проходим по всем страницам
                for page in range(self.config['start_page'], self.config['end_page'] + 1):
                    # Добавляем случайную задержку
                    self.random_delay()
                    
                    # Скрапим страницу
                    product_info = self.scrape_page(page)
                    if product_info:
                        self.products.append(product_info)
                        
                        # Сохраняем промежуточные результаты
                        if len(self.products) % self.config['save_interval'] == 0:
                            # self.save_to_excel(self.config['excel_output'])  # Временно отключено
                            self.save_to_database(self.products[-self.config['batch_size']:])
                    
                    # Обновляем прогресс-бар
                    pbar.update(1)
                    
                    # Проверяем необходимость паузы между батчами
                    self.current_batch += 1
                    self.batch_delay()
            
            # Сохраняем финальные результаты
            if self.products:
                # self.save_to_excel(self.config['excel_output'])  # Временно отключено
                self.save_to_database(self.products[-self.config['batch_size']:])
                
            logger.info(f"Скрапинг завершен. Обработано страниц: {total_pages}, собрано продуктов: {len(self.products)}")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при работе скрапера: {e}")
            raise

def main():
    try:
        scraper = PenguinMagicScraper()
        scraper.run()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 