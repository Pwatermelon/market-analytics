import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
import httpx
import os
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
import asyncio
import json

load_dotenv()

API_TOKEN = os.getenv("TG_BOT_TOKEN")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:9000")

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Хранилище для товаров (можно заменить на state, если нужно)
user_products = {}

def reviews_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад к товарам", callback_data="back_to_products")]
    ])

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Введи название товара для поиска по маркетплейсам Wildberries и Яндекс.Маркет."
    )

@dp.message(F.text)
async def search_products(message: types.Message):
    query = message.text.strip()
    await message.answer("🔎 Ищу товары...")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.get(f"{GATEWAY_URL}/search", params={"q": query})
            data = resp.json()
    except (httpx.ReadTimeout, httpx.HTTPStatusError, json.JSONDecodeError):
        await message.answer("⏳ Сервис временно недоступен, попробуйте позже.")
        return
    products = data.get("products", [])
    if not products:
        await message.answer("Ничего не найдено 😔")
        return
    user_products[message.from_user.id] = products
    # Для каждого товара отправляем отдельное сообщение с фото и кнопкой
    for p in products:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Показать отзывы", callback_data=f"product_{p['product_id']}_{p['source']}")]
        ])
        link = p.get('link', '')
        caption = f"<b>{p['title']}</b>\n{p['price']} [{p['source'].upper()}]"
        if link:
            caption += f"\n<a href='{link}'>Открыть на маркетплейсе</a>"
        try:
            await message.answer_photo(photo=p['img'], caption=caption, reply_markup=kb)
        except Exception:
            await message.answer(caption, reply_markup=kb)

@dp.callback_query(F.data.startswith("product_"))
async def show_reviews(callback: types.CallbackQuery):
    _, product_id, source = callback.data.split("_", 2)
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.get(f"{GATEWAY_URL}/reviews", params={"product_id": product_id, "source": source})
            data = resp.json()
    except (httpx.ReadTimeout, httpx.HTTPStatusError, json.JSONDecodeError):
        await callback.message.answer("⏳ Сервис временно недоступен, попробуйте позже.")
        return
    reviews = data.get("reviews", [])
    text = "<b>Отзывы:</b>\n\n"
    if not reviews:
        text += "Нет отзывов."
    else:
        for r in reviews[:10]:
            stars = "⭐" * r.get("stars", 0)
            text += f"{stars}\n{r.get('text', '')}\n\n"
    kb = reviews_keyboard()
    await callback.message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "back_to_products")
async def back_to_products(callback: types.CallbackQuery):
    products = user_products.get(callback.from_user.id, [])
    for p in products:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Показать отзывы", callback_data=f"product_{p['product_id']}_{p['source']}")]
        ])
        link = p.get('link', '')
        caption = f"<b>{p['title']}</b>\n{p['price']} [{p['source'].upper()}]"
        if link:
            caption += f"\n<a href='{link}'>Открыть на маркетплейсе</a>"
        try:
            await callback.message.answer_photo(photo=p['img'], caption=caption, reply_markup=kb)
        except Exception:
            await callback.message.answer(caption, reply_markup=kb)
    await callback.message.delete()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot)) 