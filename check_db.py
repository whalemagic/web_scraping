from database.db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Проверка состояния базы данных"""
    try:
        db = DatabaseManager()
        db.connect()
        logger.info("Подключение к базе данных...")
        
        # Проверяем количество записей
        count = db.execute_query("SELECT COUNT(*) as count FROM products", fetch_one=True)
        print(f"\nКоличество записей в базе данных: {count['count']}")
        
        # Проверяем текущее значение последовательности
        seq = db.execute_query("SELECT last_value FROM products_id_seq", fetch_one=True)
        print(f"Текущее значение последовательности ID: {seq['last_value']}")
        
        if count['count'] == 0:
            print("\nБаза данных пуста!")
        else:
            print("\nВНИМАНИЕ: В базе данных есть записи!")
            
            # Показываем первые 5 записей
            products = db.execute_query("""
                SELECT id, name, created_at 
                FROM products 
                ORDER BY id 
                LIMIT 5
            """)
            
            print("\nПервые 5 записей:")
            for p in products:
                print(f"ID: {p['id']} - {p['name']} (создан: {p['created_at']})")
        
        db.disconnect()
        logger.info("Соединение с базой данных закрыто")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке базы данных: {e}")

if __name__ == "__main__":
    check_database() 