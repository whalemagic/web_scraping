import pandas as pd
import os
from config import SCRAPER_CONFIG

def check_excel_rows():
    excel_files = [
        'data/products.xlsx',
        'data/products_export.xlsx'
    ]
    
    for file_path in excel_files:
        try:
            print(f"\nПроверка файла: {file_path}")
            
            # Проверяем существование файла
            if not os.path.exists(file_path):
                print(f"Файл {file_path} не найден")
                continue
            
            # Читаем Excel файл
            df = pd.read_excel(file_path)
            
            # Выводим количество строк
            print(f"Количество строк: {len(df)}")
            
            # Выводим последние 5 строк для проверки
            print("\nПоследние 5 строк:")
            print(df.tail())
            
        except Exception as e:
            print(f"Ошибка при проверке файла {file_path}: {str(e)}")

if __name__ == "__main__":
    check_excel_rows() 