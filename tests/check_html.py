import requests
from bs4 import BeautifulSoup
import json

def check_html():
    url = "https://www.penguinmagic.com/p/15000"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Сохраняем HTML для анализа
            with open('output/page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"HTML сохранен в output/page.html")
            
            # Анализируем структуру
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Проверяем разные селекторы для названия
            print("\nПоиск названия продукта:")
            selectors = [
                ('div#product_name h1', soup.select('div#product_name h1')),
                ('h1.product-title', soup.select('h1.product-title')),
                ('h1', soup.select('h1')),
                ('.product-name', soup.select('.product-name'))
            ]
            
            for selector, elements in selectors:
                print(f"\nСелектор '{selector}':")
                for i, el in enumerate(elements):
                    print(f"  {i+1}. {el.text.strip() if el else 'Не найдено'}")
            
            # Проверяем разные селекторы для цены
            print("\nПоиск цены:")
            price_selectors = [
                ('td.ourprice', soup.select('td.ourprice')),
                ('.product-price', soup.select('.product-price')),
                ('#price', soup.select('#price')),
                ('.price', soup.select('.price'))
            ]
            
            for selector, elements in price_selectors:
                print(f"\nСелектор '{selector}':")
                for i, el in enumerate(elements):
                    print(f"  {i+1}. {el.text.strip() if el else 'Не найдено'}")
            
        else:
            print(f"Ошибка при получении страницы: {response.status_code}")
            
    except Exception as e:
        print(f"Ошибка при проверке HTML: {e}")

if __name__ == "__main__":
    check_html() 