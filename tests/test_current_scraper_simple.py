"""
Упрощенный тест текущего скрипта парсинга без зависимости от БД
Сохраняет результаты для сравнения
"""
import sys
from pathlib import Path
import json
from datetime import datetime
import io

# Устанавливаем UTF-8 для вывода в Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Добавляем путь к корневой директории проекта
sys.path.append(str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional

FIXTURES_DIR = Path(__file__).parent / "fixtures"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Тестовые страницы
TEST_PAGES = [
    "https://www.penguinmagic.com/p/10016",
    "https://www.penguinmagic.com/p/15234",
    "https://www.penguinmagic.com/p/1452",
    "https://www.penguinmagic.com/p/21889"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

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

def test_current_scraper():
    """Запускает текущий скрипт парсинга на тестовых страницах"""
    print("=" * 80)
    print("Тестирование текущего скрипта парсинга")
    print("=" * 80)
    
    results = []
    
    for url in TEST_PAGES:
        print(f"\nОбработка страницы: {url}")
        page_id = url.split('/')[-1]
        
        try:
            # Делаем запрос
            response = requests.get(url, headers=HEADERS, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Ошибка: статус код {response.status_code}")
                results.append({
                    "url": url,
                    "page_id": page_id,
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
                continue
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Используем текущий метод парсинга
            product_info = extract_product_info(soup, url)
            
            if product_info:
                print(f"✅ Успешно распарсено:")
                print(f"   Название: {product_info.get('name', 'N/A')}")
                print(f"   Цена: ${product_info.get('price', 'N/A')}")
                print(f"   Автор: {product_info.get('author', 'N/A')}")
                desc = product_info.get('description', 'N/A')
                if desc and len(desc) > 100:
                    desc = desc[:100] + "..."
                print(f"   Описание: {desc}")
                
                result = {
                    "url": url,
                    "page_id": page_id,
                    "success": True,
                    "product_info": product_info,
                    "parsed_at": datetime.now().isoformat()
                }
            else:
                print(f"❌ Не удалось распарсить страницу")
                result = {
                    "url": url,
                    "page_id": page_id,
                    "success": False,
                    "error": "extract_product_info вернул None"
                }
            
            results.append(result)
            
            # Сохраняем результат для каждой страницы
            output_file = OUTPUT_DIR / f"current_scraper_result_{page_id}.json"
            output_file.write_text(
                json.dumps(result, indent=2, ensure_ascii=False, default=str),
                encoding='utf-8'
            )
            print(f"   Результат сохранен: {output_file}")
            
        except Exception as e:
            print(f"❌ Ошибка при обработке {url}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "url": url,
                "page_id": page_id,
                "success": False,
                "error": str(e)
            })
        
        print("-" * 80)
    
    # Сохраняем сводку
    summary = {
        "tested_at": datetime.now().isoformat(),
        "total_pages": len(TEST_PAGES),
        "successful": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
        "results": results
    }
    
    summary_file = OUTPUT_DIR / "current_scraper_summary.json"
    summary_file.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8'
    )
    
    print("\n" + "=" * 80)
    print("Сводка тестирования:")
    print(f"Всего страниц: {summary['total_pages']}")
    print(f"Успешно: {summary['successful']}")
    print(f"Ошибок: {summary['failed']}")
    print(f"Сводка сохранена: {summary_file}")
    print("=" * 80)
    
    return summary

if __name__ == "__main__":
    test_current_scraper()
