from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import sys
import os

# Add parent directory to path to import common modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.browser import BrowserManager
from common.parser import YandexMarketParser

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Yandex Market Parser Service")
browser_manager = BrowserManager()

# Инициализация парсера
parser = YandexMarketParser()

class SearchRequest(BaseModel):
    query: str

class ReviewRequest(BaseModel):
    url: str

@app.post("/search")
async def search_products(request: SearchRequest) -> Dict[str, Any]:
    """
    Поиск товаров на Яндекс.Маркет
    """
    try:
        # Инициализируем браузер
        await browser_manager.initialize()
        
        # Формируем URL для поиска
        search_url = f"https://market.yandex.ru/search?text={request.query}"
        
        # Получаем результаты поиска
        result = await browser_manager.search_products(
            url=search_url,
            marketplace="yandexmarket",
            query=request.query
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Парсим результаты
        products = parser.parse_products(result["html"])
        
        return {
            "status": "success",
            "marketplace": "yandexmarket",
            "results": products,
            "total": len(products)
        }
    except Exception as e:
        logger.error(f"Error searching products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Закрываем браузер
        await browser_manager.close()

@app.post("/reviews")
async def get_reviews(request: ReviewRequest) -> Dict[str, Any]:
    """
    Получение отзывов о товаре
    """
    try:
        reviews = await parser.get_reviews(request.url)
        return {
            "status": "success",
            "marketplace": "yandexmarket",
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