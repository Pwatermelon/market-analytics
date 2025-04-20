from fastapi import APIRouter
from services.ozon_parser import OzonParser
from services.wildberries_parser import WildberriesParser
from utils.comparator import compare_products

router = APIRouter()

@router.get("/parse/ozon")
async def parse_ozon(query: str):
    parser = OzonParser()
    return parser.search(query)

@router.get("/parse/wildberries")
async def parse_wb(query: str):
    parser = WildberriesParser()
    return parser.search(query)

@router.post("/compare")
async def compare(data: dict):
    return compare_products(data["products"])
