-- Структура таблицы products:
/*
    id          - SERIAL PRIMARY KEY     - Уникальный идентификатор продукта, автоинкрементируется
    name        - VARCHAR(255) NOT NULL  - Название продукта (обязательное поле)
    author      - VARCHAR(255)           - Автор продукта
    price       - DECIMAL(10, 2)         - Цена продукта (10 цифр всего, 2 после запятой)
    url         - VARCHAR(255)           - URL страницы продукта
    image_url   - TEXT                   - URL изображения продукта
    description - TEXT                   - Описание продукта
    categories  - TEXT[]                 - Массив категорий продукта
    created_at  - TIMESTAMP             - Дата и время создания записи (автоматически)
    updated_at  - TIMESTAMP             - Дата и время последнего обновления (автоматически)
*/


SELECT count(*) FROM products;
SELECT * from products limit 10;


/*
-- Примеры запросов:

-- 1. Получить все продукты, отсортированные по дате добавления (новые первыми)
SELECT * FROM products 
ORDER BY created_at DESC;

-- 2. Получить последние 5 добавленных продуктов
SELECT name, author, price, created_at 
FROM products 
ORDER BY created_at DESC 
LIMIT 5;

-- 3. Найти все продукты определенного автора
SELECT name, price, url 
FROM products 
WHERE author LIKE '%Doan%';

-- 4. Получить статистику по ценам
SELECT 
    COUNT(*) as total_products,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM products;

-- 5. Найти продукты в определенном ценовом диапазоне
SELECT name, author, price 
FROM products 
WHERE price BETWEEN 8.00 AND 10.00
ORDER BY price ASC;

-- 6. Поиск по названию продукта (case-insensitive)
SELECT name, author, price 
FROM products 
WHERE LOWER(name) LIKE LOWER('%magic%');

-- 7. Получить количество продуктов по авторам
SELECT author, COUNT(*) as products_count 
FROM products 
GROUP BY author 
ORDER BY products_count DESC;

-- 8. Найти дубликаты продуктов по названию
SELECT name, COUNT(*) as count 
FROM products 
GROUP BY name 
HAVING COUNT(*) > 1;

-- 9. Получить продукты, добавленные за последние 24 часа
SELECT * FROM products 
WHERE created_at >= NOW() - INTERVAL '24 hours';

-- 10. Обновить цену продукта
-- UPDATE products 
-- SET price = 9.99, 
--     updated_at = CURRENT_TIMESTAMP 
-- WHERE id = 1;

-- 11. Удалить продукт
-- DELETE FROM products 
-- WHERE id = 1;

-- Примечание: Закомментированные запросы (UPDATE, DELETE) следует использовать с осторожностью,
-- предварительно проверив условия WHERE. */