from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from parsers.common.browser import BrowserManager
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseParser(ABC):
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.base_url: str = ""
        self.marketplace_name: str = ""
    
    @abstractmethod
    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Поиск товаров по запросу"""
        pass
    
    @abstractmethod
    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """Получение детальной информации о товаре"""
        pass
    
    async def _extract_price(self, price_str: str) -> float:
        """Извлечение цены из строки"""
        try:
            # Удаляем все нечисловые символы, кроме точки
            clean_price = ''.join(c for c in price_str if c.isdigit() or c == '.')
            return float(clean_price)
        except (ValueError, TypeError):
            return 0.0
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста от лишних пробелов и переносов строк"""
        if not text:
            return ""
        return " ".join(text.split())
    
    async def save_results(self, results: List[Dict[str, Any]], query: str):
        """Сохранение результатов в файл"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results_{self.marketplace_name}_{timestamp}.json"
        
        output = {
            "marketplace": self.marketplace_name,
            "query": query,
            "timestamp": timestamp,
            "products": results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    @abstractmethod
    async def parse_search_page(self, html: str) -> List[Dict[str, Any]]:
        """Парсинг страницы с результатами поиска"""
        pass 