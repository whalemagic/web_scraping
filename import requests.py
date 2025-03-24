import requests
import re #регулярки
from bs4 import BeautifulSoup
from tqdm import tqdm  #для прогресс-бара
import time #sleep 1s
import pandas as pd
def author_name_from_product_name(product_name):
    match = re.search(r'by\s+(.+)', product_name)
    return match.group(1) if match else None

def get_product_details(product_url, page):
    try:
        response = requests.get(product_url)
        
        if response.status_code != 200:
            print(f"Ошибка при получении страницы {product_url}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        product_div = soup.find('div', id='product_name')
        product_name = product_div.find('h1').text.strip() if product_div and product_div.find('h1') else 'Нет данных'
        
        description_div = soup.find('div', id='product_description')
        product_description = description_div.text.strip() if description_div else 'Нет данных'
        
        price_tag = soup.find('td', class_='ourprice')
        price = price_tag.text.strip() if price_tag else "Цена не найдена."
        
        product_name = ' '.join(product_name.split())
        product_description = ' '.join(product_description.split())
        author_name = author_name_from_product_name(product_name)

        return {
            'product_name': product_name,
            'author_name': author_name,
            'price': price,
            'product_url': product_url,
            'page': page,
            'product_description': product_description,
            #категории
            #теги
            #убрать из author_name все теги
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка при запросе: {e}")
        return None

def get_all_product_details(base_url, start_page, end_page):
    product_details_list = []
    
    with tqdm(total=end_page - start_page + 1, desc="Загрузка страниц", unit="стр") as pbar:
        for page in range(start_page, end_page + 1):
            product_url = f"{base_url}/{page}"
            product_details = get_product_details(product_url, page)
            if product_details:
                product_details_list.append(product_details)
            pbar.update(1)  # Обновляем прогресс-бар
            time.sleep(1.5)  # Пауза в 1 секунду перед следующим запросом
    return product_details_list

if __name__ == "__main__":
    base_url = "https://www.penguinmagic.com/p" #пингвины
    start_page = 5001
    end_page = 6000
    product_details_list = get_all_product_details(base_url, start_page, end_page)
    
pd.DataFrame(product_details_list).query('product_name!="Нет данных"').to_excel("penguins2k-4k.xlsx")
def clean_description(text):
    # Удаляем HTML-теги, если они остались
    text = re.sub(r'<[^>]+>', '', text)
    
    # Удаляем специальные символы и лишние пробелы
    text = re.sub(r'[^\w\s.,!?-]', ' ', text)
    text = ' '.join(text.split())
    
    # Удаляем повторяющиеся знаки препинания
    text = re.sub(r'([.,!?])\1+', r'\1', text)
    
    return text

def extract_categories(description):
    # Список ключевых слов для категорий
    categories = {
        'card_magic': ['card', 'deck', 'playing cards', 'карты', 'колода'],
        'mentalism': ['mind reading', 'prediction', 'ментализм', 'предсказание'],
        'close_up': ['close-up', 'close up', 'клоуз-ап', 'фокусы вблизи'],
        'stage_magic': ['stage', 'platform', 'сцена', 'для сцены'],
        'coins': ['coin', 'монета', 'монеты'],
        'props': ['prop', 'реквизит', 'аксессуар'],
        'books': ['book', 'книга', 'обучение'],
        'downloads': ['download', 'instant', 'digital', 'цифровой продукт']
    }
    
    found_categories = []
    description_lower = description.lower()
    
    for category, keywords in categories.items():
        if any(keyword.lower() in description_lower for keyword in keywords):
            found_categories.append(category)
    
    return found_categories if found_categories else ['uncategorized']

# Обновляем обработку описания и добавляем категории
product_description = clean_description(product_description)
categories = extract_categories(product_description)

# Обновляем возвращаемый словарь
return {
    'product_name': product_name,
    'author_name': author_name,
    'price': price,
    'product_url': product_url,
    'page': page,
    'product_description': product_description,
    'categories': categories
}


