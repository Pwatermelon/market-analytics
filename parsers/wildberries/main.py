from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import random
import time
import urllib.parse
from typing import List, Optional
import sys
import os

# Добавляем путь к общим модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.browser import BrowserManager
from common.parser import WildberriesParser

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Wildberries Parser Service")

class ProductSearch(BaseModel):
    query: str

class Product(BaseModel):
    id: str
    name: str
    price: float
    marketplace: str = "wildberries"
    url: str
    description: Optional[str] = None
    rating: Optional[float] = None

@app.post("/search", response_model=List[Product])
async def search_products(search: ProductSearch):
    try:
        logger.info(f"Searching for: {search.query}")
        
        # Добавляем случайную задержку
        delay = random.uniform(2, 5)
        logger.info(f"Adding delay of {delay} seconds")
        time.sleep(delay)
        
        # Кодируем поисковый запрос
        encoded_query = urllib.parse.quote(search.query)
        
        # URL для поиска
        search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={encoded_query}"
        
        # Инициализируем менеджер браузера
        browser_manager = BrowserManager()
        
        # Получаем HTML страницы
        result = await browser_manager.search_products(search_url, "wildberries", search.query)
        
        if result["status"] == "error":
            logger.error(f"Error searching products: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch data from Wildberries: {result.get('error', 'Unknown error')}")
        
        # Парсим HTML
        parser = WildberriesParser()
        products_data = parser.parse_products(result["html"])
        
        # Преобразуем в модели Pydantic
        products = []
        for product_data in products_data:
            try:
                product = Product(**product_data)
                products.append(product)
            except Exception as e:
                logger.error(f"Error converting product data to Pydantic model: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Successfully parsed {len(products)} products")
        
        # Преобразуем в JSON
        products_json = [product.dict() for product in products]
        logger.info(f"Returning {len(products_json)} products as JSON")
        return products_json
        
    except Exception as e:
        logger.error(f"Error in search_products: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 