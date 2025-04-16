from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Table, ForeignKey, Boolean, JSON
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Параметры подключения к базе данных
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'magic_products_db')

# Создание URL для подключения к базе данных
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создание движка базы данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Таблица связи между продуктами и категориями
product_category = Table(
    'product_category',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    products = relationship("Product", secondary=product_category, back_populates="categories")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String)
    author_name = Column(String)
    price = Column(String)
    product_url = Column(String, unique=True)
    page = Column(Integer)
    product_description = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Новые поля
    is_in_stock = Column(Boolean, default=True)
    reviews_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    date_added = Column(DateTime)
    views_count = Column(Integer, default=0)
    discount = Column(String)
    
    # Техническая информация
    dimensions = Column(String)
    weight = Column(String)
    materials = Column(String)
    difficulty_level = Column(String)
    duration = Column(String)
    product_format = Column(String)
    
    # Метаданные
    images = Column(JSON)  # Список URL изображений
    video_url = Column(String)
    pdf_url = Column(String)
    pages_count = Column(Integer)
    language = Column(String)
    
    categories = relationship("Category", secondary=product_category, back_populates="products")

def save_to_database(data: list) -> None:
    """Сохранение данных в базу"""
    db = SessionLocal()
    try:
        for item in data:
            # Создаем или получаем категории
            categories = []
            for category_name in item['categories']:
                category = db.query(Category).filter(Category.name == category_name).first()
                if not category:
                    category = Category(name=category_name)
                    db.add(category)
                    db.flush()
                categories.append(category)

            # Создаем продукт
            product = Product(
                product_name=item['product_name'],
                author_name=item['author_name'],
                price=item['price'],
                product_url=item['product_url'],
                page=item['page'],
                product_description=item['product_description'],
                categories=categories
            )
            db.add(product)
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# Создание таблиц
Base.metadata.create_all(bind=engine)

class Database:
    def __init__(self):
        self.SessionLocal = SessionLocal

    def search_products(self, query: str, category: str = None) -> list:
        """
        Поиск продуктов по запросу и категории
        """
        db = self.SessionLocal()
        try:
            # Базовый запрос
            search_query = db.query(Product)
            
            # Добавляем фильтр по поисковому запросу
            if query:
                search_query = search_query.filter(
                    (Product.product_name.ilike(f'%{query}%')) |
                    (Product.product_description.ilike(f'%{query}%')) |
                    (Product.author_name.ilike(f'%{query}%'))
                )
            
            # Добавляем фильтр по категории
            if category:
                search_query = search_query.join(Product.categories).filter(Category.name == category)
            
            # Получаем результаты
            products = search_query.all()
            
            # Форматируем результаты для JSON
            results = []
            for product in products:
                result = {
                    'name': product.product_name,
                    'description': product.product_description,
                    'author': product.author_name,
                    'url': product.product_url,
                    'price': product.price,
                    'categories': [cat.name for cat in product.categories]
                }
                results.append(result)
            
            return results
            
        finally:
            db.close() 