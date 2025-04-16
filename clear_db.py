from database.db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_database():
    """Очистка базы данных и проверка результата"""
    try:
        db = DatabaseManager()
        db.connect()
        logger.info("Подключение к базе данных...")
        
        # Очистка таблицы products
        db.execute_query("DELETE FROM products")
        db.conn.commit()
        logger.info("Таблица products очищена")
        
        # Сброс последовательности ID
        db.execute_query("ALTER SEQUENCE products_id_seq RESTART WITH 1")
        db.conn.commit()
        logger.info("Последовательность ID сброшена")
        
        # Проверка количества записей
        count = db.execute_query("SELECT COUNT(*) as count FROM products", fetch_one=True)
        print(f"\nКоличество записей в базе после очистки: {count['count']}")
        
        if count['count'] == 0:
            print("База данных успешно очищена!")
        else:
            print(f"ВНИМАНИЕ: В базе все еще остались {count['count']} записей!")
            
            # Дополнительная информация о записях, если они остались
            if count['count'] > 0:
                remaining = db.execute_query("SELECT id, name FROM products LIMIT 5")
                print("\nПримеры оставшихся записей:")
                for r in remaining:
                    print(f"ID: {r['id']} - {r['name']}")
        
        db.disconnect()
        logger.info("Соединение с базой данных закрыто")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке базы данных: {e}")
        if db.conn:
            db.conn.rollback()

if __name__ == "__main__":
    clear_database() 