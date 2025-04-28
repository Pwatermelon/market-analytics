from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio
from parsers.ozon.parser import OzonParser
from parsers.wildberries.parser import WildberriesParser
from parsers.yandexmarket.parser import YandexMarketParser
from models.review_analyzer import ReviewAnalyzer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Market Analytics API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация парсеров и анализатора
ozon_parser = OzonParser()
wildberries_parser = WildberriesParser()
yandexmarket_parser = YandexMarketParser()
review_analyzer = ReviewAnalyzer()

class SearchRequest(BaseModel):
    query: str
    marketplaces: Optional[List[str]] = ["ozon", "wildberries", "yandexmarket"]  # По умолчанию ищем везде

class ReviewAnalysisRequest(BaseModel):
    product_url: str
    marketplace: str

@app.post("/api/parse")
async def parse_products(request: SearchRequest):
    """
    Эндпоинт для поиска товаров
    """
    try:
        all_results = []
        tasks = []

        # Создаем задачи для каждого маркетплейса
        if "ozon" in request.marketplaces:
            tasks.append(ozon_parser.search_products(request.query))
        if "wildberries" in request.marketplaces:
            tasks.append(wildberries_parser.search_products(request.query))
        if "yandexmarket" in request.marketplaces:
            tasks.append(yandexmarket_parser.search_products(request.query))

        # Запускаем все задачи параллельно
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error during parsing: {result}")
                    continue
                if isinstance(result, list):
                    all_results.extend(result)
        
        return {
            "status": "success",
            "results": all_results
        }
    except Exception as e:
        logger.error(f"Error parsing products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-reviews")
async def analyze_reviews(request: ReviewAnalysisRequest):
    """
    Эндпоинт для анализа отзывов
    """
    try:
        # Получаем отзывы в зависимости от маркетплейса
        if request.marketplace.lower() == "ozon":
            reviews = await ozon_parser.get_reviews(request.product_url)
        elif request.marketplace.lower() == "wildberries":
            reviews = await wildberries_parser.get_reviews(request.product_url)
        elif request.marketplace.lower() == "yandexmarket":
            reviews = await yandexmarket_parser.get_reviews(request.product_url)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Marketplace {request.marketplace} not supported"
            )
        
        # Анализируем отзывы
        analysis_result = await review_analyzer.analyze_reviews(reviews)
        
        return analysis_result
    except Exception as e:
        logger.error(f"Error analyzing reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Эндпоинт для проверки работоспособности сервиса
    """
    return {"status": "healthy"} 