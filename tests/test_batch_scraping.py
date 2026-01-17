"""
Тестовый скрипт для массового парсинга страниц
Парсит 50 страниц начиная с 22000 для проверки сохранения данных
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
from tqdm import tqdm
import time
import random

OUTPUT_DIR = Path(__file__).parent / "output" / "batch_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Импортируем функции парсинга из test_current_scraper_simple.py
sys.path.append(str(Path(__file__).parent))
from test_current_scraper_simple import extract_product_info, extract_reviews

def test_batch_scraping(start_id: int = 22000, count: int = 50):
    """Тестирует парсинг множества страниц"""
    print("=" * 80)
    print(f"Тестирование массового парсинга: {count} страниц начиная с {start_id}")
    print("=" * 80)
    
    results = []
    successful = 0
    failed = 0
    skipped = 0
    
    # Создаем прогресс-бар
    with tqdm(total=count, desc="Парсинг страниц", unit="страница") as pbar:
        for i in range(count):
            page_id = start_id + i
            url = f"https://www.penguinmagic.com/p/{page_id}"
            
            try:
                # Делаем запрос с задержкой
                if i > 0:
                    delay = random.uniform(1.0, 2.5)
                    time.sleep(delay)
                
                response = requests.get(url, headers=HEADERS, timeout=30)
                
                if response.status_code == 404:
                    skipped += 1
                    pbar.set_postfix({"Успешно": successful, "Ошибок": failed, "Пропущено": skipped})
                    pbar.update(1)
                    continue
                
                if response.status_code != 200:
                    failed += 1
                    results.append({
                        "page_id": page_id,
                        "url": url,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    })
                    pbar.set_postfix({"Успешно": successful, "Ошибок": failed, "Пропущено": skipped})
                    pbar.update(1)
                    continue
                
                # Парсим HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Используем текущий метод парсинга
                product_info = extract_product_info(soup, url)
                
                if product_info:
                    successful += 1
                    result = {
                        "page_id": page_id,
                        "url": url,
                        "success": True,
                        "product_info": product_info,
                        "parsed_at": datetime.now().isoformat()
                    }
                else:
                    failed += 1
                    result = {
                        "page_id": page_id,
                        "url": url,
                        "success": False,
                        "error": "extract_product_info вернул None"
                    }
                
                results.append(result)
                pbar.set_postfix({"Успешно": successful, "Ошибок": failed, "Пропущено": skipped})
                pbar.update(1)
                
            except Exception as e:
                failed += 1
                results.append({
                    "page_id": page_id,
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
                pbar.set_postfix({"Успешно": successful, "Ошибок": failed, "Пропущено": skipped})
                pbar.update(1)
    
    # Сохраняем результаты
    summary = {
        "tested_at": datetime.now().isoformat(),
        "start_id": start_id,
        "count": count,
        "total_pages": count,
        "successful": successful,
        "failed": failed,
        "skipped": skipped,
        "results": results
    }
    
    summary_file = OUTPUT_DIR / f"batch_test_summary_{start_id}_{count}.json"
    summary_file.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8'
    )
    
    # Сохраняем только успешные результаты
    successful_results = [r for r in results if r.get("success")]
    if successful_results:
        successful_file = OUTPUT_DIR / f"batch_test_successful_{start_id}_{count}.json"
        successful_file.write_text(
            json.dumps(successful_results, indent=2, ensure_ascii=False, default=str),
            encoding='utf-8'
        )
    
    print("\n" + "=" * 80)
    print("Сводка тестирования:")
    print(f"Всего страниц: {count}")
    print(f"Успешно: {successful}")
    print(f"Ошибок: {failed}")
    print(f"Пропущено (404): {skipped}")
    print(f"Процент успеха: {(successful/count*100):.1f}%")
    print(f"Сводка сохранена: {summary_file}")
    if successful_results:
        print(f"Успешные результаты: {successful_file}")
    print("=" * 80)
    
    return summary

if __name__ == "__main__":
    test_batch_scraping(start_id=22000, count=50)
