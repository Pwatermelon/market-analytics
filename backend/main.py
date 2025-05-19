from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from parser.wb_parser import search_wb_products, get_all_reviews
from parser.ym_parser import search_ym_products, get_all_reviews_ym
from parser.mm_parser import search_mm_products, get_all_reviews_mm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
async def search_products(q: str = Query(..., description="Поисковый запрос")):
    wb = await search_wb_products(q)
    wb_products = wb["products"] if isinstance(wb, dict) else wb
    try:
        ym = await search_ym_products(q)
        ym_products = ym["products"] if isinstance(ym, dict) else ym
        for p in ym_products:
            p["source"] = "ym"
    except Exception as e:
        ym_products = []
    try:
        mm = await search_mm_products(q)
        mm_products = mm["products"] if isinstance(mm, dict) else mm
        for p in mm_products:
            p["source"] = "mm"
    except Exception as e:
        mm_products = []
    for p in wb_products:
        p["source"] = "wb"
    return {"products": wb_products + ym_products + mm_products}

@app.get("/reviews")
async def get_reviews(product_id: str = Query(...), source: str = Query("wb")):
    if source == "ym":
        return {"reviews": await get_all_reviews_ym(product_id)}
    if source == "mm":
        return {"reviews": await get_all_reviews_mm(product_id)}
    return {"reviews": await get_all_reviews(product_id)} 