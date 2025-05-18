from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()
BACKEND_URL = "http://backend:8000"

@app.get("/search")
async def search(q: str = Query(...)):
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.get(f"{BACKEND_URL}/search", params={"q": q})
            if resp.status_code != 200:
                return JSONResponse(status_code=resp.status_code, content={"error": "Backend error", "details": resp.text})
            data = resp.json()
            return data
    except httpx.RequestError as e:
        return JSONResponse(status_code=503, content={"error": "Backend unavailable", "details": str(e)})

@app.get("/reviews")
async def reviews(product_id: str = Query(...), source: str = Query("wb")):
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.get(f"{BACKEND_URL}/reviews", params={"product_id": product_id, "source": source})
            if resp.status_code != 200:
                return JSONResponse(status_code=resp.status_code, content={"error": "Backend error", "details": resp.text})
            data = resp.json()
            return data
    except httpx.RequestError as e:
        return JSONResponse(status_code=503, content={"error": "Backend unavailable", "details": str(e)}) 