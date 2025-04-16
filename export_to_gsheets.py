import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def export_to_gsheets():
    load_dotenv()
    
    try:
        # Подключение к PostgreSQL
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        
        # Получаем данные из базы
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    id,
                    name,
                    author,
                    price,
                    url,
                    image_url,
                    description,
                    categories,
                    created_at,
                    updated_at
                FROM products
                ORDER BY id
            """)
            products = cur.fetchall()
            
        # Подключение к Google Sheets
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        # Путь к файлу с учетными данными Google API
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json', scope)
        
        client = gspread.authorize(credentials)
        
        # Создаем новую таблицу
        spreadsheet = client.create('Penguin Magic Products')
        worksheet = spreadsheet.get_worksheet(0)
        
        # Заголовки столбцов
        headers = [
            'ID', 'Название', 'Автор', 'Цена', 'URL', 
            'URL изображения', 'Описание', 'Категории',
            'Дата создания', 'Дата обновления'
        ]
        worksheet.append_row(headers)
        
        # Заполняем данные
        for product in products:
            row = [
                product['id'],
                product['name'],
                product['author'],
                product['price'],
                product['url'],
                product['image_url'],
                product['description'],
                ', '.join(product['categories']) if product['categories'] else '',
                product['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                product['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            ]
            worksheet.append_row(row)
        
        # Настраиваем форматирование
        worksheet.format('A1:J1', {
            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
            'textFormat': {'bold': True}
        })
        
        # Автоматически подгоняем ширину столбцов
        worksheet.columns_auto_resize(1, 10)
        
        print(f"\nДанные успешно экспортированы в Google Sheets")
        print(f"URL таблицы: {spreadsheet.url}")
        
    except Exception as e:
        print(f"Ошибка при экспорте данных: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    export_to_gsheets() 