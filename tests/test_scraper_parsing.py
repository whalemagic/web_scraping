"""
Тест для проверки парсинга реальных HTML страниц
"""
import unittest
from pathlib import Path
import sys
import json

# Добавляем путь к корневой директории проекта
sys.path.append(str(Path(__file__).parent.parent))

# Импортируем метод парсинга напрямую (без DatabaseManager)
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from typing import Dict, Optional

# Копируем функцию extract_reviews из optimized_scraper.py
def extract_reviews(soup):
    """Извлекает отзывы и оценки из HTML"""
    reviews = []
    
    try:
        # Ищем контейнер с отзывами
        reviews_container = soup.find('div', id='sorted-reviews')
        if not reviews_container:
            return reviews
        
        # Ищем все отзывы - каждый отзыв это div.product_review, который НЕ является review_header
        review_divs = reviews_container.find_all('div', class_='product_review')
        
        # Фильтруем только родительские отзывы (не review_header)
        parent_reviews = []
        for div in review_divs:
            # Если это review_header, пропускаем (это дочерний элемент)
            if 'review_header' in div.get('class', []):
                continue
            # Проверяем, что внутри есть review_header или review_body
            if div.find('div', class_='review_header') or div.find('div', class_='review_body'):
                parent_reviews.append(div)
        
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
        print(f"Ошибка при извлечении отзывов: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return reviews

# Копируем метод extract_product_info из optimized_scraper.py
def extract_product_info(soup, url):
    """Копия метода extract_product_info из optimized_scraper.py"""
    try:
        # Название продукта
        product_name = None
        
        # 1. Ищем в основном контейнере продукта
        product_container = soup.find('div', class_='product-main')
        if product_container:
            title_element = product_container.find('h1')
            if title_element:
                product_name = title_element.text.strip()
        
        # 2. Ищем в мета-тегах
        if not product_name:
            meta_title = soup.find('meta', {'property': 'og:title'})
            if meta_title:
                product_name = meta_title.get('content', '').strip()
                product_name = product_name.replace(' - Penguin Magic Shop', '').strip()
        
        # 3. Ищем в заголовке страницы
        if not product_name:
            title_element = soup.find('title')
            if title_element:
                product_name = title_element.text.strip()
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
                        price = max(float(p) for p in price_matches)
                        break
                    except (ValueError, TypeError):
                        continue
        
        if not price:
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
        reviews = extract_reviews(soup)
        
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
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        return product_info
        
    except Exception as e:
        print(f"Ошибка при извлечении информации о продукте {url}: {str(e)}")
        return None

FIXTURES_DIR = Path(__file__).parent / "fixtures"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

class TestScraperParsing(unittest.TestCase):
    """Тесты для парсинга реальных HTML страниц"""
    
    @classmethod
    def setUpClass(cls):
        """Загружаем тестовые страницы"""
        cls.test_pages = [
            {"id": "10016", "name": "Baffling Blocks"},
            {"id": "15234", "name": "Blank Prediction"},
            {"id": "1452", "name": "Unknown"}
        ]
        cls.results = []
    
    def test_parse_page_10016(self):
        """Тест парсинга страницы 10016 (Baffling Blocks)"""
        self._test_parse_page("10016", "Baffling Blocks")
    
    def test_parse_page_15234(self):
        """Тест парсинга страницы 15234 (Blank Prediction)"""
        self._test_parse_page("15234", "Blank Prediction")
    
    def test_parse_page_1452(self):
        """Тест парсинга страницы 1452"""
        self._test_parse_page("1452", "Unknown")
    
    def test_parse_page_21889(self):
        """Тест парсинга страницы 21889 (Leviosa Phone)"""
        self._test_parse_page("21889", "Leviosa Phone")
    
    def _test_parse_page(self, page_id: str, expected_name_contains: str):
        """Общий метод для тестирования парсинга страницы"""
        html_file = FIXTURES_DIR / f"page_{page_id}.html"
        
        if not html_file.exists():
            self.skipTest(f"HTML файл не найден: {html_file}. Запустите download_test_pages.py")
        
        # Загружаем HTML
        html_content = html_file.read_text(encoding='utf-8')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Формируем URL
        url = f"https://www.penguinmagic.com/p/{page_id}"
        
        # Парсим страницу
        product_info = extract_product_info(soup, url)
        
        # Сохраняем результат
        result = {
            "page_id": page_id,
            "url": url,
            "product_info": product_info,
            "parsed_successfully": product_info is not None
        }
        
        # Сохраняем в JSON
        output_file = OUTPUT_DIR / f"parsed_page_{page_id}.json"
        output_file.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str),
            encoding='utf-8'
        )
        
        # Проверяем результат
        self.assertIsNotNone(product_info, f"Не удалось распарсить страницу {page_id}")
        self.assertIn('name', product_info, "Отсутствует поле 'name'")
        self.assertIn('price', product_info, "Отсутствует поле 'price'")
        self.assertIn('url', product_info, "Отсутствует поле 'url'")
        
        # Проверяем, что название не пустое
        self.assertIsNotNone(product_info['name'], "Название продукта пустое")
        self.assertNotEqual(product_info['name'], "Название не найдено", "Название не найдено")
        
        # Проверяем, что цена найдена (может быть 0.0, но должна быть)
        self.assertIsNotNone(product_info['price'], "Цена не найдена")
        self.assertIsInstance(product_info['price'], (int, float), "Цена должна быть числом")
        
        # Проверяем URL
        self.assertEqual(product_info['url'], url, "URL не совпадает")
        
        print(f"\n✅ Страница {page_id} успешно распарсена:")
        print(f"   Название: {product_info['name']}")
        print(f"   Цена: ${product_info['price']}")
        print(f"   Автор: {product_info.get('author', 'Не указан')}")
        print(f"   Результат сохранен: {output_file}")
        
        # Сохраняем для сводки
        TestScraperParsing.results.append(result)
    
    @classmethod
    def tearDownClass(cls):
        """Сохраняем сводку всех результатов"""
        if cls.results:
            summary = {
                "total_pages": len(cls.results),
                "successful": sum(1 for r in cls.results if r['parsed_successfully']),
                "failed": sum(1 for r in cls.results if not r['parsed_successfully']),
                "results": cls.results
            }
            
            summary_file = OUTPUT_DIR / "parsing_summary.json"
            summary_file.write_text(
                json.dumps(summary, indent=2, ensure_ascii=False, default=str),
                encoding='utf-8'
            )
            
            print("\n" + "=" * 80)
            print("Сводка парсинга:")
            print(f"Всего страниц: {summary['total_pages']}")
            print(f"Успешно: {summary['successful']}")
            print(f"Ошибок: {summary['failed']}")
            print(f"Сводка сохранена: {summary_file}")
            print("=" * 80)

if __name__ == '__main__':
    unittest.main(verbosity=2)
