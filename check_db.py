from database.db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_records():
    with DatabaseManager() as db:
        # Проверяем количество записей в таблице products
        query = "SELECT COUNT(*) as count FROM products"
        result = db.execute_query(query, fetch_one=True)
        
        if result:
            count = result['count']
            logger.info(f"В базе данных найдено {count} записей")
            
            if count > 0:
                # Получаем первые 5 записей для примера
                query = "SELECT * FROM products LIMIT 5"
                products = db.execute_query(query)
                logger.info("\nПримеры записей:")
                for product in products:
                    logger.info(f"ID: {product['id']}, Название: {product['name']}, Цена: {product['price']}")
        else:
            logger.warning("Не удалось получить количество записей")

if __name__ == "__main__":
    check_database_records() 