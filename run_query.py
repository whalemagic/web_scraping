from database.db_manager import DatabaseManager
import logging
import pandas as pd
from tabulate import tabulate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_queries(queries: list):
    """
    Выполняет список SQL-запросов в рамках одного соединения
    
    Args:
        queries (list): Список SQL-запросов для выполнения
    """
    with DatabaseManager() as db:
        for i, query in enumerate(queries, 1):
            print(f"\n{'='*80}")
            print(f"Запрос #{i}:")
            print(f"{'='*80}")
            print(f"SQL: {query.strip()}")
            print(f"{'='*80}")
            
            try:
                result = db.execute_query(query)
                if result:
                    # Преобразуем результат в DataFrame
                    df = pd.DataFrame(result)
                    
                    # Выводим результат в виде таблицы
                    print("\nРезультат:")
                    print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))
                else:
                    print("Запрос выполнен успешно, но не вернул результатов")
            except Exception as e:
                print(f"Ошибка при выполнении запроса: {e}")

# Примеры запросов
if __name__ == "__main__":
    # Список запросов для выполнения
    queries = [
  
        """
        SELECT *
        FROM products 
        ORDER BY created_at DESC 
        LIMIT 10;
        """
    ]
    
    # Выполняем все запросы в одном соединении
    execute_queries(queries)