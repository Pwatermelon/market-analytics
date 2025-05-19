from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from transformers import pipeline
import os
import traceback

app = FastAPI()

# Маппинг лейблов для rubert-tiny2
LABEL_MAP = {
    "LABEL_0": "Позитивный",
    "LABEL_1": "Негативный",
    "LABEL_2": "Нейтральный"
}

# Загружаем пайплайны (можно заменить на другие модели при необходимости)
summarizer = pipeline("summarization", model="cointegrated/rut5-base-paraphraser")
sentiment = pipeline("sentiment-analysis", model="cointegrated/rubert-tiny2")

@app.post("/analyze")
async def analyze_reviews(request: Request):
    data = await request.json()
    reviews = data.get("reviews", [])
    print("Получено отзывов:", len(reviews))
    print("Пример отзыва:", reviews[0] if reviews else "нет отзывов")
    texts = list({r.get("text", "") for r in reviews if r.get("text")})  # только уникальные
    print("Количество отзывов для суммаризации:", len(texts))
    all_text = " ".join(texts)[:4000]  # ограничение на длину
    print("Текст для суммаризации (первые 500 символов):", all_text[:500])
    if not texts:
        return JSONResponse({"summary": "Нет отзывов для анализа.", "verdict": "Нет данных"})
    try:
        summary = summarizer(all_text, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
        verdict = sentiment(summary)[0]
        verdict_label = verdict['label']
        verdict_text = LABEL_MAP.get(verdict_label, verdict_label)
        return {"summary": summary, "verdict": verdict_text}
    except Exception as e:
        print("Ошибка анализа:", e)
        print(traceback.format_exc())
        return JSONResponse({"summary": "Ошибка анализа.", "verdict": str(e)}, status_code=500) 