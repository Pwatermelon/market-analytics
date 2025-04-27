from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from typing import List, Optional
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Market Analytics API Gateway")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductSearch(BaseModel):
    query: str
    marketplace: Optional[str] = None

class Product(BaseModel):
    id: str
    name: str
    price: float
    marketplace: str
    url: str
    description: Optional[str] = None
    rating: Optional[float] = None

@app.post("/search", response_model=List[Product])
async def search_products(search: ProductSearch):
    results = []
    async with httpx.AsyncClient() as client:
        tasks = []
        
        if not search.marketplace or search.marketplace == "ozon":
            tasks.append(client.post(
                f"{os.getenv('OZON_PARSER_URL')}/search",
                json={"query": search.query}
            ))
        
        if not search.marketplace or search.marketplace == "wildberries":
            tasks.append(client.post(
                f"{os.getenv('WILDBERRIES_PARSER_URL')}/search",
                json={"query": search.query}
            ))
        
        if not search.marketplace or search.marketplace == "goldapple":
            tasks.append(client.post(
                f"{os.getenv('GOLDAPPLE_PARSER_URL')}/search",
                json={"query": search.query}
            ))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for response in responses:
            if isinstance(response, Exception):
                continue
            if response.status_code == 200:
                results.extend(response.json())
    
    return results

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 