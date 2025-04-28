from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

app = FastAPI(title="Yandex Market Parser")
browser_manager = BrowserManager()

class SearchRequest(BaseModel):
    query: str

@app.post("/search")
async def search_products(request: SearchRequest):
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
        parser = YandexMarketParser()
        products = parser.parse_products(result["html"])
        
        return {
            "status": "success",
            "products": products,
            "total": len(products)
        }
        
    except Exception as e:
        logger.error(f"Error processing search request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Закрываем браузер
        await browser_manager.close()

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 