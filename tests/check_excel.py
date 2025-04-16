import pandas as pd
import os

def check_excel():
    file_path = 'output/products.xlsx'
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден")
        return
        
    try:
        df = pd.read_excel(file_path)
        print(f"\nРазмер файла: {os.path.getsize(file_path)} байт")
        print(f"Количество строк: {len(df)}")
        print(f"Количество столбцов: {len(df.columns)}")
        print("\nНазвания столбцов:")
        for col in df.columns:
            print(f"- {col}")
            
        if len(df) > 0:
            print("\nДанные о продуктах:")
            print("-" * 80)
            for _, row in df.iterrows():
                print(f"Название: {row['name']}")
                print(f"Автор: {row['author'] if pd.notna(row['author']) else 'Не указан'}")
                print(f"Цена: ${row['price']}")
                print(f"URL: {row['url']}")
                print("-" * 80)
            
            # Статистика по ценам
            price_stats = df['price'].describe()
            print("\nСтатистика по ценам:")
            print(f"Среднее: ${price_stats['mean']:.2f}")
            print(f"Минимум: ${price_stats['min']:.2f}")
            print(f"Максимум: ${price_stats['max']:.2f}")
            
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")

if __name__ == "__main__":
    check_excel() 