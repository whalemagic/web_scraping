-- Добавление столбца subcategory в таблицу products
ALTER TABLE products
ADD COLUMN IF NOT EXISTS subcategory VARCHAR(100);

-- Добавление индекса для ускорения поиска по подкатегории
CREATE INDEX IF NOT EXISTS idx_products_subcategory ON products(subcategory); 