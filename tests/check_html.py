import requests
from bs4 import BeautifulSoup
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_html_structure(url: str):
    """Проверка структуры HTML страницы"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        logger.info(f"Отправка запроса к {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Сохраняем HTML в файл для анализа
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        html_file = output_dir / 'page.html'
        html_file.write_text(response.text, encoding='utf-8')
        logger.info(f"HTML сохранен в {html_file}")
        
        # Парсим HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Проверяем основные элементы
        logger.info("\nПроверка основных элементов:")
        
        # Все div с классами
        logger.info("\nВсе div с классами:")
        divs_with_class = soup.find_all('div', class_=True)
        for div in divs_with_class[:10]:  # Показываем первые 10
            logger.info(f"Class: {div.get('class')}")
        
        # Все заголовки
        logger.info("\nВсе заголовки:")
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for header in headers[:10]:
            logger.info(f"Tag: {header.name}, Class: {header.get('class')}, Text: {header.text.strip()[:100]}")
        
        # Все элементы с ценой
        logger.info("\nВсе элементы с возможной ценой:")
        price_candidates = soup.find_all(['span', 'div', 'p'], string=lambda text: text and '$' in text)
        for price in price_candidates[:10]:
            logger.info(f"Tag: {price.name}, Class: {price.get('class')}, Text: {price.text.strip()}")
        
        # Все изображения
        logger.info("\nВсе изображения:")
        images = soup.find_all('img')
        for img in images[:10]:
            logger.info(f"Class: {img.get('class')}, Src: {img.get('src')}")
        
        # Все ссылки
        logger.info("\nВсе ссылки:")
        links = soup.find_all('a')
        for link in links[:10]:
            logger.info(f"Class: {link.get('class')}, Href: {link.get('href')}, Text: {link.text.strip()[:50]}")
            
    except Exception as e:
        logger.error(f"Ошибка при проверке HTML: {e}")

if __name__ == "__main__":
    # Проверяем страницу продукта
    product_url = "https://www.penguinmagic.com/p/15001"
    check_html_structure(product_url) 