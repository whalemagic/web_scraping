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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class Scraper:
    def __init__(self, config: Dict = SCRAPER_CONFIG):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config['headers'])
        
    def clean_text(self, text: Optional[str]) -> str:
        if not text:
            return 'Нет данных'
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\w\s.,!?-]', ' ', text)
        text = re.sub(r'([.,!?])\1+', r'\1', text)
        return ' '.join(text.split())

    def extract_author(self, product_name: str) -> Optional[str]:
        if not product_name:
            return None
            
        for pattern in AUTHOR_PATTERNS:
            if match := re.search(pattern, product_name, re.IGNORECASE):
                author = match.group(1).strip()
                author = re.sub(r'\s+', ' ', author)
                author = re.sub(r'^[|-\s]+|[|-\s]+$', '', author)
                return author if author else None
        
        return None

    def extract_categories(self, description: str) -> List[str]:
        description_lower = description.lower()
        return [cat for cat, keywords in CATEGORIES.items() 
                if any(keyword.lower() in description_lower for keyword in keywords)] or ['uncategorized']

    def get_product_details(self, product_url: str, page: int) -> Optional[Dict]:
        try:
            response = self.session.get(product_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            product_name = self.clean_text(soup.find('div', id='product_name').find('h1').text if soup.find('div', id='product_name') else None)
            description = self.clean_text(soup.find('div', id='product_description').text if soup.find('div', id='product_description') else None)
            price = self.clean_text(soup.find('td', class_='ourprice').text if soup.find('td', class_='ourprice') else None)
            author_name = self.extract_author(product_name)

            return {
                'product_name': product_name,
                'author_name': author_name,
                'price': price,
                'product_url': product_url,
                'page': page,
                'product_description': description,
                'categories': self.extract_categories(description)
            }
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при запросе {product_url}: {e}")
            return None
        except Exception as e:
            logging.error(f"Неожиданная ошибка при обработке {product_url}: {e}")
            return None

    def get_all_product_details(self) -> List[Dict]:
        product_details_list = []
        start_page, end_page = self.config['start_page'], self.config['end_page']
        
        with tqdm(total=end_page - start_page + 1, desc="Загрузка страниц", unit="стр") as pbar:
            for page in range(start_page, end_page + 1):
                if details := self.get_product_details(f"{self.config['base_url']}/{page}", page):
                    product_details_list.append(details)
                pbar.update(1)
                time.sleep(self.config['delay'])
        return product_details_list

    def save_results(self, data: List[Dict]) -> None:
        try:
            df = pd.DataFrame(data)
            df = df.query('product_name!="Нет данных"')
            df.to_excel(self.config['output_file'], index=False)
            logging.info(f"Результаты сохранены в {self.config['output_file']}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении результатов: {e}")

def main():
    try:
        scraper = Scraper()
        logging.info("Начало работы скрапера")
        
        product_details_list = scraper.get_all_product_details()
        scraper.save_results(product_details_list)
        
        logging.info("Работа скрапера завершена успешно")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main() 