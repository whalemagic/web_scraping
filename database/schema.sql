-- Удаляем существующую таблицу
DROP TABLE IF EXISTS products CASCADE;

-- Создание таблицы products со всеми необходимыми полями
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    price DECIMAL(10, 2),
    url VARCHAR(255),
    image_url TEXT,
    description TEXT,
    categories TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем индекс для ускорения поиска по названию
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

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