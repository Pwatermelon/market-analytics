import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
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

# Хранилище для товаров и отзывов
user_products = {}

REVIEWS_PER_PAGE = 5

# --- Новый UX ---
def build_products_keyboard(products):
    keyboard = []
    for idx, p in enumerate(products):
        keyboard.append([
            InlineKeyboardButton(
                text=f"{p['title']} ({p['price']}) [{p['source'].upper()}]",
                callback_data=f"show_{idx}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Введи название товара для поиска по маркетплейсам Wildberries, Яндекс.Маркет и Magnit Market."
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
    # Оставляем только по 5 с каждого source
    grouped = {"wb": [], "ym": [], "mm": []}
    for p in products:
        if p["source"] in grouped and len(grouped[p["source"]]) < 5:
            grouped[p["source"]].append(p)
    short_products = grouped["wb"] + grouped["ym"] + grouped["mm"]
    if not short_products:
        await message.answer("Ничего не найдено 😔")
        return
    user_products[message.from_user.id] = {"products": short_products, "reviews": {}}
    # Media group (до 10 фоток за раз, поэтому делаем только первые 10)
    media = [InputMediaPhoto(media=p['img'], caption=p['title']) for p in short_products[:10]]
    if media:
        await message.answer_media_group(media)
    # Основное сообщение с кнопками и списком
    text = "Найденные товары:\n\n" + "\n".join(
        [f"{i+1}. {p['title']} ({p['price']}) [{p['source'].upper()}]" for i, p in enumerate(short_products)]
    )
    kb = build_products_keyboard(short_products)
    main_msg = await message.answer(text, reply_markup=kb)
    # Сохраняем id основного сообщения для edit
    user_products[message.from_user.id]["main_msg_id"] = main_msg.message_id

@dp.callback_query(F.data.startswith("show_"))
async def show_product(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    user_data = user_products.get(callback.from_user.id, {})
    products = user_data.get("products", [])
    main_msg_id = user_data.get("main_msg_id")
    if not products or idx >= len(products) or not main_msg_id:
        await callback.answer("Ошибка: товар не найден.")
        return
    p = products[idx]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Показать отзывы", callback_data=f"reviews_{idx}")],
        [InlineKeyboardButton(text="Анализ отзывов", callback_data=f"analyze_{idx}")],
        [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_list")]
    ])
    text = f"<b>{p['title']}</b>\n{p['price']} [{p['source'].upper()}]\n<a href='{p['link']}'>Открыть на маркетплейсе</a>"
    await callback.bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=main_msg_id,
        text=text,
        reply_markup=kb,
        parse_mode='HTML'
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_list")
async def back_to_list(callback: types.CallbackQuery):
    user_data = user_products.get(callback.from_user.id, {})
    products = user_data.get("products", [])
    main_msg_id = user_data.get("main_msg_id")
    if not products or not main_msg_id:
        await callback.answer("Нет товаров.")
        return
    kb = build_products_keyboard(products)
    text = "Найденные товары:\n\n" + "\n".join(
        [f"{i+1}. {p['title']} ({p['price']}) [{p['source'].upper()}]" for i, p in enumerate(products)]
    )
    await callback.bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=main_msg_id,
        text=text,
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("reviews_"))
async def show_reviews(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    user_data = user_products.get(callback.from_user.id, {})
    products = user_data.get("products", [])
    main_msg_id = user_data.get("main_msg_id")
    if not products or idx >= len(products) or not main_msg_id:
        await callback.answer("Ошибка: товар не найден.")
        return
    p = products[idx]
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.get(f"{GATEWAY_URL}/reviews", params={"product_id": p['product_id'], "source": p['source']})
            data = resp.json()
    except Exception:
        await callback.answer("Ошибка получения отзывов.")
        return
    reviews = data.get("reviews", [])
    text = "<b>Отзывы:</b>\n\n"
    if not reviews:
        text += "Нет отзывов."
    else:
        for r in reviews[:5]:
            stars = "⭐" * r.get("stars", 0)
            text += f"{stars}\n{r.get('text', '')}\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад к товару", callback_data=f"show_{idx}")],
        [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_list")]
    ])
    await callback.bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=main_msg_id,
        text=text,
        reply_markup=kb,
        parse_mode='HTML'
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("analyze_"))
async def analyze_reviews(callback: types.CallbackQuery):
    idx = int(callback.data.split("_")[1])
    user_data = user_products.get(callback.from_user.id, {})
    products = user_data.get("products", [])
    main_msg_id = user_data.get("main_msg_id")
    if not products or idx >= len(products) or not main_msg_id:
        await callback.answer("Ошибка: товар не найден.")
        return
    p = products[idx]
    await callback.bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=main_msg_id,
        text="🤖 Анализирую отзывы...",
        reply_markup=None
    )
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.get(f"{GATEWAY_URL}/reviews", params={"product_id": p['product_id'], "source": p['source']})
            reviews_data = resp.json()
            reviews = reviews_data.get("reviews", [])
    except Exception:
        await callback.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=main_msg_id,
            text="Ошибка получения отзывов.",
            reply_markup=None
        )
        await callback.answer()
        return
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post("http://review-analyzer:8500/analyze", json={"reviews": reviews})
            result = resp.json()
    except Exception:
        await callback.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=main_msg_id,
            text="Ошибка анализа отзывов.",
            reply_markup=None
        )
        await callback.answer()
        return
    summary = result.get("summary", "?")
    verdict = result.get("verdict", "?")
    text = f"<b>📝 Краткая выжимка:</b>\n{summary}\n\n<b>🏆 Вердикт:</b> {verdict}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад к товару", callback_data=f"show_{idx}")],
        [InlineKeyboardButton(text="Назад к списку", callback_data="back_to_list")]
    ])
    await callback.bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=main_msg_id,
        text=text,
        reply_markup=kb,
        parse_mode='HTML'
    )
    await callback.answer()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot)) 