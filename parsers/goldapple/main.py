from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup
import json
import random
import time
from typing import List, Optional

app = FastAPI(title="Gold Apple Parser Service")

class ProductSearch(BaseModel):
    query: str

class Product(BaseModel):
    id: str
    name: str
    price: float
    marketplace: str = "goldapple"
    url: str
    description: Optional[str] = None
    rating: Optional[float] = None

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]

async def get_random_user_agent():
    return random.choice(USER_AGENTS)

async def parse_ga_product(product_data):
    try:
        product_id = product_data.get("id", "")
        name = product_data.get("name", "")
        price = float(product_data.get("price", {}).get("value", 0))
        brand = product_data.get("brand", {}).get("name", "")
        
        return Product(
            id=product_id,
            name=f"{brand} {name}".strip(),
            price=price,
            url=f"https://goldapple.ru/product/{product_id}",
            description=product_data.get("description", ""),
            rating=None  # Gold Apple обычно не показывает рейтинги
        )
    except Exception as e:
        print(f"Error parsing Gold Apple product: {e}")
        return None

@app.post("/search", response_model=List[Product])
async def search_products(search: ProductSearch):
    try:
        # Добавляем случайную задержку
        time.sleep(random.uniform(1, 3))
        
        headers = {
            "User-Agent": await get_random_user_agent(),
            "Accept": "application/json",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://goldapple.ru",
            "Referer": "https://goldapple.ru/",
        }
        
        # Используем API Gold Apple для поиска
        search_url = f"https://goldapple.ru/api/catalog/search?q={search.query}&page=1&per_page=10"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Gold Apple")
            
            data = response.json()
            products_data = data.get("items", [])
            
            results = []
            for product_data in products_data:
                product = await parse_ga_product(product_data)
                if product:
                    results.append(product)
            
            return results
            
    except Exception as e:
        print(f"Error in search_products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 