"""
Скрипт для загрузки тестовых HTML страниц локально
"""
import requests
from pathlib import Path
import json
from datetime import datetime

# Создаем директорию для фикстур
FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)

# Тестовые страницы
TEST_PAGES = [
    {
        "url": "https://www.penguinmagic.com/p/10016",
        "id": "10016",
        "name": "Baffling Blocks"
    },
    {
        "url": "https://www.penguinmagic.com/p/15234",
        "id": "15234",
        "name": "Blank Prediction"
    },
    {
        "url": "https://www.penguinmagic.com/p/1452",
        "id": "1452",
        "name": "Unknown"
    }
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def download_page(url: str, page_id: str) -> dict:
    """Загружает HTML страницу и сохраняет локально"""
    try:
        print(f"Загрузка страницы {url}...")
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            # Сохраняем HTML
            html_file = FIXTURES_DIR / f"page_{page_id}.html"
            html_file.write_text(response.text, encoding='utf-8')
            print(f"✅ HTML сохранен: {html_file}")
            
            # Сохраняем метаданные
            metadata = {
                "url": url,
                "page_id": page_id,
                "status_code": response.status_code,
                "content_length": len(response.text),
                "downloaded_at": datetime.now().isoformat(),
                "headers": dict(response.headers)
            }
            
            metadata_file = FIXTURES_DIR / f"page_{page_id}_metadata.json"
            metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
            print(f"✅ Метаданные сохранены: {metadata_file}")
            
            return {
                "success": True,
                "html_file": str(html_file),
                "metadata_file": str(metadata_file),
                "content_length": len(response.text)
            }
        else:
            print(f"❌ Ошибка: статус код {response.status_code}")
            return {
                "success": False,
                "status_code": response.status_code,
                "error": f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        print(f"❌ Ошибка при загрузке {url}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Загружает все тестовые страницы"""
    import sys
    import io
    # Устанавливаем UTF-8 для вывода в Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 80)
    print("Загрузка тестовых HTML страниц")
    print("=" * 80)
    
    results = []
    
    for page in TEST_PAGES:
        print(f"\nОбработка страницы {page['id']}: {page['name']}")
        result = download_page(page['url'], page['id'])
        result['page_info'] = page
        results.append(result)
        print("-" * 80)
    
    # Сохраняем сводку
    summary = {
        "downloaded_at": datetime.now().isoformat(),
        "total_pages": len(TEST_PAGES),
        "successful": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
        "results": results
    }
    
    summary_file = FIXTURES_DIR / "download_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print("\n" + "=" * 80)
    print("Сводка загрузки:")
    print(f"Всего страниц: {summary['total_pages']}")
    print(f"Успешно: {summary['successful']}")
    print(f"Ошибок: {summary['failed']}")
    print(f"Сводка сохранена: {summary_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()
