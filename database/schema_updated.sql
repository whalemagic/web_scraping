-- Обновленная схема БД с поддержкой новых полей
-- Удаляем существующую таблицу
DROP TABLE IF EXISTS products CASCADE;

-- Создание таблицы products со всеми необходимыми полями
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    price DECIMAL(10, 2),
    discounted_price DECIMAL(10, 2),  -- Цена со скидкой
    url VARCHAR(255) UNIQUE,
    image_url TEXT,
    description TEXT,
    tags TEXT[],  -- Изменено с categories на tags
    reviews JSONB,  -- Отзывы и оценки в формате JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_url ON products(url);
CREATE INDEX IF NOT EXISTS idx_products_tags ON products USING GIN(tags);  -- GIN индекс для массива
CREATE INDEX IF NOT EXISTS idx_products_reviews ON products USING GIN(reviews);  -- GIN индекс для JSONB

-- Создаем функцию для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Удаляем триггер, если он существует
DROP TRIGGER IF EXISTS update_products_updated_at ON products;

-- Создаем триггер для автоматического обновления updated_at
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
