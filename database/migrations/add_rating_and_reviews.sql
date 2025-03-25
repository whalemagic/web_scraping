-- Добавление столбцов rating и reviews_count в таблицу products
ALTER TABLE products
ADD COLUMN IF NOT EXISTS rating DECIMAL(3, 2),
ADD COLUMN IF NOT EXISTS reviews_count INTEGER DEFAULT 0;

-- Добавление индексов для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_products_rating ON products(rating);
CREATE INDEX IF NOT EXISTS idx_products_reviews_count ON products(reviews_count); 