from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import json
import random
import time
from typing import List, Optional

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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]

async def get_random_user_agent():
    return random.choice(USER_AGENTS)

async def parse_wb_product(product_data):
    try:
        product_id = str(product_data.get("id", ""))
        name = product_data.get("name", "")
        price = float(product_data.get("salePriceU", 0)) / 100  # Цена в копейках
        rating = product_data.get("rating", 0) / 10 if product_data.get("rating") else None
        brand = product_data.get("brand", "")
        
        return Product(
            id=product_id,
            name=f"{brand} {name}".strip(),
            price=price,
            url=f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
            description=product_data.get("description", ""),
            rating=rating
        )
    except Exception as e:
        print(f"Error parsing WB product: {e}")
        return None

@app.post("/search", response_model=List[Product])
async def search_products(search: ProductSearch):
    try:
        # Добавляем случайную задержку
        time.sleep(random.uniform(1, 3))
        
        headers = {
            "User-Agent": await get_random_user_agent(),
            "Accept": "*/*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://www.wildberries.ru",
            "Referer": "https://www.wildberries.ru/",
        }
        
        # Используем API Wildberries для поиска
        search_url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?query={search.query}&resultset=catalog&limit=10"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(search_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Wildberries")
            
            data = response.json()
            products_data = data.get("data", {}).get("products", [])
            
            results = []
            for product_data in products_data:
                product = await parse_wb_product(product_data)
                if product:
                    results.append(product)
            
            return results
            
    except Exception as e:
        print(f"Error in search_products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 