"""
Тест экспорта данных в Excel
"""
import sys
from pathlib import Path
import json
import pandas as pd
from datetime import datetime

# Добавляем путь к корневой директории проекта
sys.path.append(str(Path(__file__).parent.parent))

OUTPUT_DIR = Path(__file__).parent / "output" / "excel_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def test_excel_export():
    """Тестирует экспорт данных в Excel"""
    print("=" * 80)
    print("Тестирование экспорта в Excel")
    print("=" * 80)
    
    # Загружаем результаты из batch теста
    batch_file = Path(__file__).parent / "output" / "batch_test" / "batch_test_successful_22000_50.json"
    
    if not batch_file.exists():
        print(f"❌ Файл с результатами не найден: {batch_file}")
        print("   Сначала запустите test_batch_scraping.py")
        return
    
    # Читаем данные
    with open(batch_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Извлекаем product_info из результатов
    products = [r['product_info'] for r in results if r.get('success')]
    
    print(f"Загружено {len(products)} продуктов для экспорта")
    
    # Создаем DataFrame
    df = pd.DataFrame(products)
    
    # Определяем столбцы
    columns = ['name', 'author', 'price', 'discounted_price', 'url', 'image_url', 'description', 'tags', 'reviews']
    df = df.reindex(columns=columns)
    
    # Обрабатываем reviews - преобразуем в строку JSON для Excel
    if 'reviews' in df.columns:
        df['reviews'] = df['reviews'].apply(
            lambda x: json.dumps(x, ensure_ascii=False) if x else None
        )
    
    # Обрабатываем tags - преобразуем список в строку
    if 'tags' in df.columns:
        df['tags'] = df['tags'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) else (x if x else None)
        )
    
    # Очищаем текст от специальных символов
    def clean_text(text):
        if pd.isna(text):
            return text
        text = str(text)
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = ''.join(char for char in text if ord(char) < 65536)
        text = ' '.join(text.split())
        return text
    
    # Применяем очистку к текстовым полям
    for col in ['name', 'author', 'description', 'tags']:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)
    
    # Сохраняем в Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = OUTPUT_DIR / f"products_export_{timestamp}.xlsx"
    
    try:
        df.to_excel(excel_file, index=False, engine='openpyxl')
        print(f"✅ Данные успешно экспортированы в Excel: {excel_file}")
        print(f"   Всего записей: {len(df)}")
        print(f"   Столбцы: {', '.join(df.columns)}")
        
        # Проверяем размер файла
        file_size = excel_file.stat().st_size / 1024  # KB
        print(f"   Размер файла: {file_size:.2f} KB")
        
        # Показываем статистику
        print("\nСтатистика:")
        print(f"   Продуктов с ценой: {df['price'].notna().sum()}")
        print(f"   Продуктов со скидкой: {df['discounted_price'].notna().sum()}")
        print(f"   Продуктов с тегами: {df['tags'].notna().sum()}")
        print(f"   Продуктов с отзывами: {df['reviews'].notna().sum()}")
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте в Excel: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("=" * 80)

if __name__ == "__main__":
    test_excel_export()
