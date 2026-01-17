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
            
            # Цена без скидки (List price) и цена со скидкой (Price)
            price = None  # Цена без скидки (List price)
            discounted_price = None  # Цена со скидкой (Price)
            
            # 1. Ищем в таблице product_price_details (приоритетный источник)
            price_table = soup.find('table', class_='product_price_details')
            if price_table:
                # Ищем все строки таблицы
                rows = price_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value_cell = cells[1]
                        
                        # List price (цена без скидки) - обычно в <strike> теге
                        if 'list price' in label:
                            strike_tag = value_cell.find('strike')
                            if strike_tag:
                                try:
                                    price_text = strike_tag.get_text(strip=True)
                                    price = float(re.sub(r'[^\d.]', '', price_text))
                                except (ValueError, TypeError):
                                    pass
                            # Если нет strike, берем из самой ячейки
                            elif not price:
                                try:
                                    price_text = value_cell.get_text(strip=True)
                                    price = float(re.sub(r'[^\d.]', '', price_text))
                                except (ValueError, TypeError):
                                    pass
                        
                        # Price (цена со скидкой) - в ячейке с классом ourprice
                        elif 'price:' in label and value_cell.get('class') and 'ourprice' in value_cell.get('class'):
                            try:
                                price_text = value_cell.get_text(strip=True)
                                discounted_price = float(re.sub(r'[^\d.]', '', price_text))
                            except (ValueError, TypeError):
                                pass
            
            # 2. Если не нашли в таблице, ищем в JSON-данных
            if not price or not discounted_price:
                script_tags = soup.find_all('script', {'type': 'application/ld+json'})
                for script in script_tags:
                    try:
                        json_data = json.loads(script.string)
                        if isinstance(json_data, dict):
                            if 'offers' in json_data:
                                offers = json_data['offers']
                                if isinstance(offers, dict):
                                    # Цена со скидкой обычно в 'price'
                                    if 'price' in offers and not discounted_price:
                                        try:
                                            discounted_price = float(offers['price'])
                                        except (ValueError, TypeError):
                                            pass
                                    # Цена без скидки может быть в 'priceSpecification'
                                    if 'priceSpecification' in offers:
                                        price_spec = offers['priceSpecification']
                                        if isinstance(price_spec, dict) and 'price' in price_spec and not price:
                                            try:
                                                price = float(price_spec['price'])
                                            except (ValueError, TypeError):
                                                pass
                                break
                    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
                        continue
            
            # 3. Если не нашли цену без скидки, используем цену со скидкой как основную
            if not price and discounted_price:
                price = discounted_price
                discounted_price = None  # Если нет скидки, не сохраняем discounted_price
            
            # 4. Fallback: ищем цену в мета-тегах
            if not price:
                meta_price = soup.find('meta', {'property': 'product:price:amount'})
                if meta_price:
                    try:
                        price = float(meta_price.get('content'))
                    except (ValueError, TypeError):
                        pass
            
            # 5. Fallback: ищем в элементах с ценой
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
            
            # 6. Fallback: ищем цену в тексте страницы с помощью регулярных выражений
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
            
            # Описание - ищем полное описание в div#product_description
            description = None
            description_div = soup.find('div', id='product_description')
            if description_div:
                # Ищем первый параграф в product_subsection
                product_subsection = description_div.find('div', class_='product_subsection')
                if product_subsection:
                    description_p = product_subsection.find('p')
                    if description_p:
                        # Получаем весь текст, заменяем <br> на пробелы
                        description = description_p.get_text(separator=' ', strip=True)
                        # Очищаем от лишних пробелов
                        description = ' '.join(description.split())
            
            # Если не нашли полное описание, используем meta как fallback
            if not description:
                description_meta = soup.find('meta', {'property': 'og:description'})
                if description_meta:
                    description = description_meta.get('content').strip()
            
            # Теги - ищем ссылки на /tricks/tagged/ рядом с продуктом
            # Теги продукта находятся в div с float:left после product_addtocart
            # Каждый тег в отдельном div с стилем: border:1px solid #999; background:#aaa
            # НЕ в навигационном меню (browse_menu)
            tags = []
            
            # Ищем область с тегами продукта - div с float:left после product_addtocart
            # Теги находятся в div с float:left, который содержит div'ы с серыми блоками
            product_addtocart = soup.find('div', class_='product_addtocart')
            if product_addtocart:
                # Ищем следующий div с float:left после product_addtocart
                # Это контейнер с тегами продукта
                tags_container = None
                # Ищем все div с float:left после product_addtocart
                for sibling in product_addtocart.find_all_next('div'):
                    style = sibling.get('style', '')
                    if 'float:left' in style:
                        # Проверяем, что это не навигация
                        if sibling.find_parent('div', id='browse_menu'):
                            continue
                        # Проверяем, что внутри есть div'ы с серыми блоками (теги)
                        gray_blocks = sibling.find_all('div', style=lambda s: s and 'background:#aaa' in s and 'border:1px solid #999' in s)
                        if gray_blocks:
                            tags_container = sibling
                            break
                
                if tags_container:
                    # Извлекаем все ссылки на /tricks/tagged/ из этого контейнера
                    tag_links = tags_container.find_all('a', href=lambda x: x and '/tricks/tagged/' in x)
                    for link in tag_links:
                        tag_text = link.get_text(strip=True)
                        if tag_text:
                            tags.append(tag_text)
            
            # Удаляем дубликаты, сохраняя порядок
            tags = list(dict.fromkeys(tags))
            
            # Отзывы и оценки
            reviews = self.extract_reviews(soup)
            
            product_info = {
                'name': product_name,
                'author': author,
                'price': price,  # Цена без скидки (List price)
                'discounted_price': discounted_price,  # Цена со скидкой (если есть)
                'url': url,
                'image_url': image_url,
                'description': description,
                'tags': tags,
                'reviews': reviews,  # Отзывы и оценки
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            logger.info(f"Извлечена информация о продукте: {product_name} (${price})")
            return product_info
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации о продукте {url}: {str(e)}")
            return None

    def extract_reviews(self, soup) -> List[Dict]:
        """Извлекает отзывы и оценки из HTML"""
        reviews = []
        
        try:
            # Ищем контейнер с отзывами
            reviews_container = soup.find('div', id='sorted-reviews')
            if not reviews_container:
                logger.debug("Контейнер sorted-reviews не найден")
                return reviews
            
            logger.debug(f"Найден контейнер sorted-reviews, ищем отзывы...")
            
            # Ищем все отзывы - каждый отзыв это div.product_review, который НЕ является review_header
            # Структура: <div class="product_review"> содержит <div class="product_review review_header"> и <div class="review_body">
            review_divs = reviews_container.find_all('div', class_='product_review')
            logger.debug(f"Найдено {len(review_divs)} div с классом product_review")
            
            # Фильтруем только родительские отзывы (не review_header)
            parent_reviews = []
            for div in review_divs:
                # Если это review_header, пропускаем (это дочерний элемент)
                if 'review_header' in div.get('class', []):
                    continue
                # Проверяем, что внутри есть review_header или review_body
                if div.find('div', class_='review_header') or div.find('div', class_='review_body'):
                    parent_reviews.append(div)
            
            logger.debug(f"Найдено {len(parent_reviews)} родительских отзывов")
            
            for review_div in parent_reviews:
                review_data = {}
                
                # Извлекаем оценку (rating) из изображения звезд в review_header
                rating = None
                review_header = review_div.find('div', class_='review_header')
                if review_header:
                    star_img = review_header.find('img', src=lambda x: x and 'stars.gif' in x)
                    if star_img:
                        src = star_img.get('src', '')
                        # Извлекаем число из названия файла (например, "5stars.gif" -> 5)
                        rating_match = re.search(r'(\d+)stars\.gif', src)
                        if rating_match:
                            rating = int(rating_match.group(1))
                    
                    # Извлекаем заголовок отзыва
                    subject = None
                    subject_span = review_header.find('span', class_='review_subject')
                    if subject_span:
                        subject = subject_span.get_text(strip=True)
                    
                    # Извлекаем дату
                    date = None
                    review_from = review_header.find('div', class_='review_from')
                    if review_from:
                        # Ищем текст после "on"
                        text = review_from.get_text()
                        date_match = re.search(r'on\s+([A-Za-z]+\s+\d+[a-z]{0,2},\s+\d{4})', text)
                        if date_match:
                            date = date_match.group(1)
                        
                        # Проверяем, является ли покупатель верифицированным
                        verified_spans = review_from.find_all('span', class_='review_verified')
                        verified_buyer = any('Verified buyer' in span.get_text() for span in verified_spans)
                    else:
                        verified_buyer = False
                else:
                    subject = None
                    date = None
                    verified_buyer = False
                
                # Извлекаем текст отзыва
                review_text = None
                review_body = review_div.find('div', class_='review_body')
                if review_body:
                    # Получаем весь текст, заменяем <br> на пробелы
                    review_text = review_body.get_text(separator=' ', strip=True)
                    # Очищаем от лишних пробелов
                    review_text = ' '.join(review_text.split())
                
                # Извлекаем количество полезных голосов
                helpful_count = None
                helpful_total = None
                # Ищем текст вида "X of Y magicians found this helpful"
                helpful_text = review_div.get_text()
                helpful_match = re.search(r'(\d+)\s+of\s+(\d+)\s+magicians\s+found\s+this\s+helpful', helpful_text)
                if helpful_match:
                    helpful_count = int(helpful_match.group(1))
                    helpful_total = int(helpful_match.group(2))
                
                # Собираем данные отзыва
                if rating or review_text:  # Добавляем отзыв, если есть хотя бы оценка или текст
                    review_data = {
                        'rating': rating,
                        'subject': subject,
                        'text': review_text,
                        'date': date,
                        'verified_buyer': verified_buyer,
                        'helpful_count': helpful_count,
                        'helpful_total': helpful_total
                    }
                    reviews.append(review_data)
            
            logger.debug(f"Извлечено {len(reviews)} отзывов")
            
            # Также извлекаем общую оценку из review_summary
            overall_rating = None
            review_count = None
            review_summary = soup.find('div', id='review_summary')
            if review_summary:
                summary_link = review_summary.find('a', href='#reviews')
                if summary_link:
                    summary_text = summary_link.get_text(strip=True)
                    # Ищем паттерн "4.8 stars / 6 reviews"
                    rating_match = re.search(r'([\d.]+)\s+stars?\s*/\s*(\d+)\s+reviews?', summary_text)
                    if rating_match:
                        overall_rating = float(rating_match.group(1))
                        review_count = int(rating_match.group(2))
            
            # Добавляем общую информацию в начало списка отзывов (если есть)
            if overall_rating is not None:
                reviews.insert(0, {
                    'type': 'summary',
                    'overall_rating': overall_rating,
                    'total_reviews': review_count
                })
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении отзывов: {str(e)}")
        
        return reviews

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
            
            # Определяем столбцы (включая новые поля)
            columns = ['name', 'author', 'price', 'discounted_price', 'url', 'image_url', 'description', 'tags', 'reviews']
            new_df = new_df.reindex(columns=columns)
            
            # Обрабатываем reviews - преобразуем в строку JSON для Excel
            if 'reviews' in new_df.columns:
                new_df['reviews'] = new_df['reviews'].apply(
                    lambda x: json.dumps(x, ensure_ascii=False) if x else None
                )
            
            # Обрабатываем tags - преобразуем список в строку
            if 'tags' in new_df.columns:
                new_df['tags'] = new_df['tags'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else (x if x else None)
                )
            
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
            
            # Применяем очистку к текстовым полям (кроме reviews, которое уже в JSON)
            for col in ['name', 'author', 'description', 'tags']:
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
                            self.save_to_excel(self.config['excel_output'])
                            self.save_to_database(self.products[-self.config['batch_size']:])
                    
                    # Обновляем прогресс-бар
                    pbar.update(1)
                    
                    # Проверяем необходимость паузы между батчами
                    self.current_batch += 1
                    self.batch_delay()
            
            # Сохраняем финальные результаты
            if self.products:
                self.save_to_excel(self.config['excel_output'])
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