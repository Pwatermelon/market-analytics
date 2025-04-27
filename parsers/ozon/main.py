from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import re
from typing import List, Optional
import json
import random
import time

app = FastAPI(title="Ozon Parser Service")

class ProductSearch(BaseModel):
    query: str

class Product(BaseModel):
    id: str
    name: str
    price: float
    marketplace: str = "ozon"
    url: str
    description: Optional[str] = None
    rating: Optional[float] = None

# Список User-Agent для ротации
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

async def get_random_user_agent():
    return random.choice(USER_AGENTS)

async def parse_ozon_product(product_data):
    try:
        product_id = product_data.get("id", "")
        name = product_data.get("title", "")
        price_data = product_data.get("price", {})
        price = float(price_data.get("price", "0").replace(" ", "").replace("₽", ""))
        rating = product_data.get("rating", {}).get("rate", None)
        description = product_data.get("description", "")
        
        return Product(
            id=product_id,
            name=name,
            price=price,
            url=f"https://www.ozon.ru/product/{product_id}/",
            description=description,
            rating=rating
        )
    except Exception as e:
        print(f"Error parsing product: {e}")
        return None

@app.post("/search", response_model=List[Product])
async def search_products(search: ProductSearch):
    try:
        # Добавляем случайную задержку для имитации человеческого поведения
        time.sleep(random.uniform(1, 3))
        
        headers = {
            "User-Agent": await get_random_user_agent(),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.ozon.ru/",
            "Origin": "https://www.ozon.ru",
        }
        
        # Формируем URL для поиска
        search_url = f"https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url=/search/?text={search.query}&page=1"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Ozon")
            
            # Парсим JSON ответ
            data = response.json()
            
            # Извлекаем данные о товарах
            products_data = []
            try:
                # Путь к данным о товарах в JSON может меняться, нужно адаптировать
                products_data = data.get("widgetState", {}).get("searchResults", [])
            except Exception as e:
                print(f"Error extracting products data: {e}")
            
            # Парсим каждый товар
            results = []
            for product_data in products_data[:10]:  # Ограничиваем количество результатов
                product = await parse_ozon_product(product_data)
                if product:
                    results.append(product)
            
            return results
            
    except Exception as e:
        print(f"Error in search_products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 