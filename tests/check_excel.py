import pandas as pd
from pathlib import Path

try:
    # Читаем Excel файл
    excel_path = Path('output/products.xlsx')
    print(f"\nЧтение файла: {excel_path}")
    
    df = pd.read_excel(excel_path)
    
    # Общая информация
    print(f"\nКоличество записей: {len(df)}")
    print(f"Колонки: {', '.join(df.columns)}")
    
    if len(df) > 0:
        print("\nПервые 5 записей:")
        print("-" * 80)
        for _, row in df.head().iterrows():
            print(f"Название: {row['name']}")
            if 'price' in row:
                print(f"Цена: ${row['price']}" if pd.notna(row['price']) else "Цена: Не указана")
            if 'url' in row:
                print(f"URL: {row['url']}")
            print("-" * 80)
            
        # Статистика по ценам
        if 'price' in df.columns:
            price_stats = df['price'].describe()
            print("\nСтатистика по ценам:")
            print(f"Среднее: ${price_stats['mean']:.2f}")
            print(f"Минимум: ${price_stats['min']:.2f}")
            print(f"Максимум: ${price_stats['max']:.2f}")
    else:
        print("\nФайл пуст")
        
except Exception as e:
    print(f"\nОшибка при чтении Excel файла: {e}") 