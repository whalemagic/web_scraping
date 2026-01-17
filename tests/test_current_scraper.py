"""
Тест текущего скрипта парсинга на реальных страницах
Сохраняет результаты для сравнения
"""
import sys
from pathlib import Path
import json
from datetime import datetime

# Добавляем путь к корневой директории проекта
sys.path.append(str(Path(__file__).parent.parent))

from optimized_scraper import PenguinMagicScraper
from bs4 import BeautifulSoup
import requests

FIXTURES_DIR = Path(__file__).parent / "fixtures"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Тестовые страницы
TEST_PAGES = [
    "https://www.penguinmagic.com/p/10016",
    "https://www.penguinmagic.com/p/15234",
    "https://www.penguinmagic.com/p/1452"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def test_current_scraper():
    """Запускает текущий скрипт парсинга на тестовых страницах"""
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 80)
    print("Тестирование текущего скрипта парсинга")
    print("=" * 80)
    
    scraper = PenguinMagicScraper()
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
            product_info = scraper.extract_product_info(soup, url)
            
            if product_info:
                print(f"✅ Успешно распарсено:")
                print(f"   Название: {product_info.get('name', 'N/A')}")
                print(f"   Цена: ${product_info.get('price', 'N/A')}")
                print(f"   Автор: {product_info.get('author', 'N/A')}")
                print(f"   Описание: {product_info.get('description', 'N/A')[:100]}...")
                
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
