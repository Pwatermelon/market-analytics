from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import random
import time
import urllib.parse
import sys
import os

# Добавляем путь к общим модулям
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.browser import BrowserManager
from .parser import WildberriesParser

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Wildberries Parser Service")

# Инициализация парсера
parser = WildberriesParser()

class SearchRequest(BaseModel):
    query: str

class ReviewRequest(BaseModel):
    url: str

class Product(BaseModel):
    id: str
    name: str
    price: float
    marketplace: str = "wildberries"
    url: str
    description: Optional[str] = None
    rating: Optional[float] = None

@app.post("/search")
async def search_products(request: SearchRequest) -> Dict[str, Any]:
    """
    Поиск товаров на Wildberries
    """
    try:
        logger.info(f"Searching for: {request.query}")
        
        # Добавляем случайную задержку
        delay = random.uniform(2, 5)
        logger.info(f"Adding delay of {delay} seconds")
        time.sleep(delay)
        
        # Кодируем поисковый запрос
        encoded_query = urllib.parse.quote(request.query)
        
        # URL для поиска
        search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={encoded_query}"
        
        # Инициализируем менеджер браузера
        browser_manager = BrowserManager()
        
        # Получаем HTML страницы
        result = await browser_manager.search_products(search_url, "wildberries", request.query)
        
        if result["status"] == "error":
            logger.error(f"Error searching products: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch data from Wildberries: {result.get('error', 'Unknown error')}")
        
        # Парсим HTML
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
        return {
            "status": "success",
            "marketplace": "wildberries",
            "results": products_json
        }
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reviews")
async def get_reviews(request: ReviewRequest) -> Dict[str, Any]:
    """
    Получение отзывов о товаре
    """
    try:
        reviews = await parser.get_reviews(request.url)
        return {
            "status": "success",
            "marketplace": "wildberries",
            "reviews": reviews
        }
    except Exception as e:
        logger.error(f"Error getting reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Проверка работоспособности сервиса
    """
    return {"status": "healthy"} 