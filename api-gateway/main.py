from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from typing import List, Optional
from pydantic import BaseModel
import asyncio
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Market Analytics API Gateway")

# Проверка переменных окружения
required_env_vars = ['OZON_PARSER_URL', 'WILDBERRIES_PARSER_URL', 'GOLDAPPLE_PARSER_URL']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

logger.info("Environment variables validated successfully")
logger.info(f"OZON_PARSER_URL: {os.getenv('OZON_PARSER_URL')}")
logger.info(f"WILDBERRIES_PARSER_URL: {os.getenv('WILDBERRIES_PARSER_URL')}")
logger.info(f"GOLDAPPLE_PARSER_URL: {os.getenv('GOLDAPPLE_PARSER_URL')}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class ProductSearch(BaseModel):
    query: str
    marketplace: Optional[str] = None

    @classmethod
    def validate(cls, value):
        if isinstance(value, dict) and value.get('marketplace') == '':
            value['marketplace'] = None
        return super().validate(value)

class Product(BaseModel):
    id: str
    name: str
    price: float
    marketplace: str
    url: str
    description: Optional[str] = None
    rating: Optional[float] = None
    image_url: Optional[str] = None

@app.post("/search", response_model=List[Product])
async def search_products(search: ProductSearch, request: Request):
    try:
        # Логируем сырой запрос до любой обработки
        logger.info("Received search request")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request URL: {request.url}")
        
        # Логируем тело запроса и заголовки
        body = await request.body()
        body_str = body.decode()
        logger.info(f"Raw request body: {body_str}")
        logger.info(f"Content-Type: {request.headers.get('content-type')}")
        logger.info(f"All headers: {dict(request.headers)}")
        
        # Пытаемся распарсить JSON
        try:
            body_json = json.loads(body_str)
            logger.info(f"Parsed JSON body: {body_json}")
            
            # Проверяем marketplace
            if 'marketplace' in body_json and body_json['marketplace'] == '':
                logger.info("Converting empty marketplace to None")
                body_json['marketplace'] = None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        logger.info(f"Parsed search request: {search}")
        
        if not search.query:
            logger.error("Empty query received")
            raise HTTPException(status_code=400, detail="Query is required")
        
        results = []
        async with httpx.AsyncClient(timeout=120.0) as client:  # Увеличиваем таймаут до 120 секунд
            tasks = []
            
            if not search.marketplace or search.marketplace == "ozon":
                ozon_url = f"{os.getenv('OZON_PARSER_URL')}/search"
                logger.info(f"Sending request to Ozon parser: {ozon_url}")
                tasks.append(client.post(
                    ozon_url,
                    json={"query": search.query}
                ))
            
            if not search.marketplace or search.marketplace == "wildberries":
                wb_url = f"{os.getenv('WILDBERRIES_PARSER_URL')}/search"
                logger.info(f"Sending request to Wildberries parser: {wb_url}")
                tasks.append(client.post(
                    wb_url,
                    json={"query": search.query}
                ))
            
            if not search.marketplace or search.marketplace == "goldapple":
                ga_url = f"{os.getenv('GOLDAPPLE_PARSER_URL')}/search"
                logger.info(f"Sending request to Gold Apple parser: {ga_url}")
                tasks.append(client.post(
                    ga_url,
                    json={"query": search.query}
                ))
            
            logger.info(f"Waiting for {len(tasks)} parser responses...")
            
            # Ждем завершения всех задач
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for response in responses:
                # Проверяем, не возникло ли исключение
                if isinstance(response, Exception):
                    logger.error(f"Error from parser: {str(response)}")
                    continue
                
                logger.info(f"Received response from parser: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"Raw parser response data type: {type(data)}")
                        logger.info(f"Raw parser response data: {json.dumps(data, ensure_ascii=False)}")
                        
                        if not isinstance(data, list):
                            logger.error(f"Invalid response format, expected list but got: {type(data)}")
                            continue
                        
                        logger.info(f"Number of products in response: {len(data)}")
                        
                        # Проверяем, что все элементы имеют необходимые поля
                        valid_products = []
                        for i, product in enumerate(data):
                            logger.info(f"Processing product {i + 1}/{len(data)}")
                            logger.info(f"Product data: {json.dumps(product, ensure_ascii=False)}")
                            try:
                                # Проверяем наличие обязательных полей
                                required_fields = ["id", "name", "price", "marketplace", "url"]
                                missing_fields = [field for field in required_fields if field not in product]
                                if missing_fields:
                                    logger.warning(f"Product missing required fields: {missing_fields}")
                                    continue
                                
                                # Преобразуем строковые значения в нужные типы
                                if isinstance(product["price"], str):
                                    try:
                                        original_price = product["price"]
                                        product["price"] = float(product["price"].replace(" ", "").replace("₽", "").replace(",", "."))
                                        logger.info(f"Converted price from '{original_price}' to {product['price']}")
                                    except (ValueError, TypeError) as e:
                                        logger.error(f"Could not convert price to float: {product['price']}, error: {str(e)}")
                                        product["price"] = 0.0
                                elif not isinstance(product["price"], (int, float)):
                                    logger.error(f"Price is not a string or number: {product['price']}, type: {type(product['price'])}")
                                    product["price"] = 0.0
                                
                                if "rating" in product and product["rating"] is not None:
                                    if isinstance(product["rating"], str):
                                        try:
                                            original_rating = product["rating"]
                                            product["rating"] = float(product["rating"].replace(",", "."))
                                            logger.info(f"Converted rating from '{original_rating}' to {product['rating']}")
                                        except (ValueError, TypeError) as e:
                                            logger.error(f"Could not convert rating to float: {product['rating']}, error: {str(e)}")
                                            product["rating"] = None
                                    elif not isinstance(product["rating"], (int, float)):
                                        logger.error(f"Rating is not a string or number: {product['rating']}, type: {type(product['rating'])}")
                                        product["rating"] = None
                                
                                valid_products.append(product)
                                logger.info(f"Successfully added product: {product['name']} (ID: {product['id']})")
                            except (ValueError, TypeError) as e:
                                logger.error(f"Error processing product: {str(e)}, product: {json.dumps(product, ensure_ascii=False)}")
                                continue
                        
                        logger.info(f"Added {len(valid_products)} valid products from parser")
                        results.extend(valid_products)
                    except Exception as e:
                        logger.error(f"Error parsing response: {str(e)}", exc_info=True)
                else:
                    logger.error(f"Parser returned non-200 status code: {response.status_code}")
        
        logger.info(f"Returning {len(results)} products")
        return results
    except Exception as e:
        logger.error(f"Unexpected error in search_products: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 