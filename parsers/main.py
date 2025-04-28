import asyncio
import logging
from typing import List, Dict, Any
from ozon.parser import OzonParser
from wildberries.parser import WildberriesParser
from yandexmarket.parser import YandexMarketParser
from common.browser import BrowserManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketplaceParser:
    def __init__(self):
        self.parsers = {
            'ozon': OzonParser(),
            'wildberries': WildberriesParser(),
            'yandexmarket': YandexMarketParser()
        }
        self.browser_manager = BrowserManager()
    
    async def initialize(self):
        """Инициализация браузера и прокси"""
        await self.browser_manager.initialize()
        # Здесь можно добавить загрузку прокси из конфига или API
    
    async def parse_all(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Запуск парсинга по всем маркетплейсам"""
        results = {}
        tasks = []
        
        for marketplace, parser in self.parsers.items():
            task = asyncio.create_task(self._parse_marketplace(marketplace, parser, query))
            tasks.append(task)
        
        # Ждем завершения всех задач
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        for marketplace, result in zip(self.parsers.keys(), completed_tasks):
            if isinstance(result, Exception):
                logger.error(f"Error parsing {marketplace}: {result}")
                results[marketplace] = []
            else:
                results[marketplace] = result
        
        return results
    
    async def _parse_marketplace(self, marketplace: str, parser: Any, query: str) -> List[Dict[str, Any]]:
        """Парсинг отдельного маркетплейса с обработкой ошибок"""
        try:
            logger.info(f"Starting parsing {marketplace} for query: {query}")
            results = await parser.search_products(query)
            logger.info(f"Finished parsing {marketplace}. Found {len(results)} products")
            return results
        except Exception as e:
            logger.error(f"Error parsing {marketplace}: {e}")
            return []
    
    async def close(self):
        """Закрытие браузера и освобождение ресурсов"""
        await self.browser_manager.close()

async def main():
    parser = MarketplaceParser()
    try:
        await parser.initialize()
        
        # Пример использования
        query = input("Введите поисковый запрос: ")
        results = await parser.parse_all(query)
        
        # Вывод результатов
        for marketplace, products in results.items():
            print(f"\n{marketplace.upper()}: Найдено {len(products)} товаров")
            for product in products[:5]:  # Показываем первые 5 товаров
                print(f"\nНазвание: {product['title']}")
                print(f"Цена: {product['price']} руб.")
                print(f"URL: {product['url']}")
                if 'rating' in product:
                    print(f"Рейтинг: {product['rating']}")
                if 'reviews_count' in product:
                    print(f"Отзывов: {product['reviews_count']}")
    
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        await parser.close()

if __name__ == "__main__":
    asyncio.run(main()) 