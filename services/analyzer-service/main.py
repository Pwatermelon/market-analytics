from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import os
from typing import Optional, List, Dict
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM
import numpy as np
from pathlib import Path

app = FastAPI(
    title="Analyzer Service",
    redirect_slashes=False  # Отключаем автоматические редиректы
)

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_analytics")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Путь к моделям
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models")

# Конфигурация моделей (можно переопределить через переменные окружения)
SENTIMENT_MODEL_NAME = os.getenv("SENTIMENT_MODEL_NAME", None)  # Если None - использует локальную
SUMMARIZER_MODEL_NAME = os.getenv("SUMMARIZER_MODEL_NAME", None)  # Если None - использует локальную

# Глобальные переменные для моделей
sentiment_model = None
sentiment_tokenizer = None
summarizer_model = None
summarizer_tokenizer = None


# Модели БД (импортируем из parser-service структуру)
class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    author = Column(String)
    rating = Column(Integer)
    text = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Поля для результатов анализа
    sentiment = Column(Float)  # -1 (негатив) до 1 (позитив)
    sentiment_label = Column(String)  # positive, negative, neutral
    summary = Column(Text)


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    marketplace = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic модели
class SentimentAnalysis(BaseModel):
    sentiment: float
    label: str


class AnalyticsResponse(BaseModel):
    product_id: int
    total_reviews: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_sentiment: float
    timeline: List[Dict]  # [{date, sentiment, count}]


class SummaryResponse(BaseModel):
    product_id: int
    summary: str
    total_reviews: int


# Утилиты
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id(x_user_id: Optional[str] = Header(None)) -> int:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID не предоставлен")
    return int(x_user_id)


def load_models():
    """Загрузка ML моделей
    
    Поддерживает:
    - Локальные модели из папки models/
    - Модели из Hugging Face по имени
    - Автоматический fallback на дефолтные модели
    """
    global sentiment_model, sentiment_tokenizer, summarizer_model, summarizer_tokenizer
    
    # Загрузка модели тональности
    print("\n1️⃣ Загрузка модели тональности...")
    sentiment_path = Path(MODEL_PATH) / "sentiment"
    
    # Приоритет 1: Локальная модель из папки
    if sentiment_path.exists() and any(sentiment_path.iterdir()):
        try:
            print(f"   📁 Локальная модель найдена: {sentiment_path}")
            sentiment_tokenizer = AutoTokenizer.from_pretrained(str(sentiment_path))
            sentiment_model = AutoModelForSequenceClassification.from_pretrained(str(sentiment_path))
            sentiment_model.eval()
            print(f"   ✅ Модель тональности загружена из {sentiment_path}")
        except Exception as e:
            print(f"   ❌ Ошибка загрузки локальной модели: {e}")
            print("   🔄 Пробую загрузить модель из Hugging Face...")
            load_sentiment_from_hf()
    # Приоритет 2: Модель из Hugging Face по имени (если указана)
    elif SENTIMENT_MODEL_NAME:
        try:
            print(f"   🌐 Загрузка из Hugging Face: {SENTIMENT_MODEL_NAME}")
            sentiment_tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_NAME)
            sentiment_model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_NAME)
            sentiment_model.eval()
            print(f"   ✅ Модель тональности загружена из Hugging Face")
        except Exception as e:
            print(f"   ❌ Ошибка загрузки из Hugging Face: {e}")
            load_sentiment_from_hf()
    # Приоритет 3: Дефолтная модель
    else:
        load_sentiment_from_hf()
    
    # Загрузка модели суммаризации
    print("\n2️⃣ Загрузка модели суммаризации...")
    summarizer_path = Path(MODEL_PATH) / "summarizer"
    
    # Приоритет 1: Локальная модель из папки
    if summarizer_path.exists() and any(summarizer_path.iterdir()):
        try:
            print(f"   📁 Локальная модель найдена: {summarizer_path}")
            summarizer_tokenizer = AutoTokenizer.from_pretrained(str(summarizer_path))
            summarizer_model = AutoModelForSeq2SeqLM.from_pretrained(str(summarizer_path))
            summarizer_model.eval()
            print(f"   ✅ Модель суммаризации загружена из {summarizer_path}")
        except Exception as e:
            print(f"   ❌ Ошибка загрузки локальной модели: {e}")
            print("   🔄 Пробую загрузить модель из Hugging Face...")
            load_summarizer_from_hf()
    # Приоритет 2: Модель из Hugging Face по имени (если указана)
    elif SUMMARIZER_MODEL_NAME:
        try:
            print(f"   🌐 Загрузка из Hugging Face: {SUMMARIZER_MODEL_NAME}")
            summarizer_tokenizer = AutoTokenizer.from_pretrained(SUMMARIZER_MODEL_NAME)
            summarizer_model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARIZER_MODEL_NAME)
            summarizer_model.eval()
            print(f"   ✅ Модель суммаризации загружена из Hugging Face")
        except Exception as e:
            print(f"   ❌ Ошибка загрузки из Hugging Face: {e}")
            load_summarizer_from_hf()
    # Приоритет 3: Дефолтная модель
    else:
        load_summarizer_from_hf()
    
    print("\n" + "=" * 60)
    print("✅ ЗАГРУЗКА МОДЕЛЕЙ ЗАВЕРШЕНА")
    print("=" * 60)


def load_sentiment_from_hf():
    """Загрузка дефолтной модели тональности из Hugging Face"""
    global sentiment_model, sentiment_tokenizer
    try:
        print("   🌐 Загрузка дефолтной модели тональности...")
        sentiment_tokenizer = AutoTokenizer.from_pretrained("blanchefort/rubert-base-cased-sentiment")
        sentiment_model = AutoModelForSequenceClassification.from_pretrained("blanchefort/rubert-base-cased-sentiment")
        sentiment_model.eval()
        print("   ✅ Дефолтная модель тональности загружена")
    except Exception as e:
        print(f"   ❌ Критическая ошибка: не удалось загрузить модель тональности: {e}")
        raise


def load_summarizer_from_hf():
    """Загрузка дефолтной модели суммаризации из Hugging Face"""
    global summarizer_model, summarizer_tokenizer
    
    # Список моделей для попытки загрузки (в порядке приоритета)
    summarizer_models = [
        "IlyaGusev/rut5_base_sum_gazeta",
        "IlyaGusev/rut5_base_sum_gazeta_v2",
        "cointegrated/rut5-base",
    ]
    
    last_error = None
    for model_name in summarizer_models:
        try:
            print(f"🔄 Попытка загрузить модель суммаризации: {model_name}")
            summarizer_tokenizer = AutoTokenizer.from_pretrained(model_name)
            print(f"✓ Токенизатор загружен для {model_name}")
            
            summarizer_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            summarizer_model.eval()
            print(f"✅ Модель суммаризации успешно загружена: {model_name}")
            return
        except Exception as e:
            last_error = e
            print(f"❌ Не удалось загрузить {model_name}: {e}")
            import traceback
            print(traceback.format_exc())
            if model_name != summarizer_models[-1]:
                print("🔄 Пробую альтернативу...")
                continue
    
    # Если все попытки не удались
    error_msg = f"Не удалось загрузить ни одну модель суммаризации. Последняя ошибка: {last_error}"
    print(f"❌ {error_msg}")
    raise Exception(error_msg)


def analyze_sentiment(text: str) -> SentimentAnalysis:
    """Анализ тональности текста"""
    if sentiment_model is None or sentiment_tokenizer is None:
        raise HTTPException(status_code=500, detail="Модель тональности не загружена")
    
    # Токенизация
    inputs = sentiment_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    
    # Предсказание
    with torch.no_grad():
        outputs = sentiment_model(**inputs)
        logits = outputs.logits
    
    # Получение вероятностей
    probs = torch.nn.functional.softmax(logits, dim=-1)
    
    # Адаптивная обработка разных типов моделей
    # Код автоматически определяет количество классов и структуру вывода
    num_classes = probs.shape[1]
    
    if num_classes == 3:
        # Трехклассовая классификация: negative, neutral, positive
        # Подходит для: blanchefort/rubert-base-cased-sentiment, большинство русских моделей
        negative_prob = probs[0][0].item()
        neutral_prob = probs[0][1].item()
        positive_prob = probs[0][2].item()
        
        # Преобразуем в шкалу от -1 до 1
        sentiment_score = positive_prob - negative_prob
        label_idx = torch.argmax(probs, dim=-1).item()
        labels = ["negative", "neutral", "positive"]
        label = labels[label_idx]
    elif num_classes == 2:
        # Бинарная классификация: negative, positive
        # Подходит для: многие бинарные модели тональности
        sentiment_score = probs[0][1].item() - probs[0][0].item()  # positive - negative
        label = "positive" if sentiment_score > 0 else "negative"
    elif num_classes == 5:
        # Пятиклассовая классификация (например, очень негатив, негатив, нейтрал, позитив, очень позитив)
        # Берем среднее значение
        if probs.shape[1] == 5:
            # Предполагаем порядок: очень негатив, негатив, нейтрал, позитив, очень позитив
            very_negative = probs[0][0].item()
            negative = probs[0][1].item()
            neutral = probs[0][2].item()
            positive = probs[0][3].item()
            very_positive = probs[0][4].item()
            
            # Взвешенная сумма
            sentiment_score = (very_positive + positive * 0.5) - (very_negative + negative * 0.5)
            label_idx = torch.argmax(probs, dim=-1).item()
            labels = ["very_negative", "negative", "neutral", "positive", "very_positive"]
            label = labels[label_idx]
        else:
            # Общий случай для 5 классов
            sentiment_score = float(logits[0][-1].item() - logits[0][0].item())
            sentiment_score = np.tanh(sentiment_score)
            label_idx = torch.argmax(probs, dim=-1).item()
            label = f"class_{label_idx}"
    else:
        # Для любых других моделей (1 класс, регрессия, и т.д.)
        # Используем первый выход как значение тональности
        if num_classes == 1:
            # Регрессионная модель - выход напрямую
            sentiment_score = float(logits[0][0].item())
            sentiment_score = np.tanh(sentiment_score)  # Нормализация в [-1, 1]
        else:
            # Многоклассовая модель - берем разницу между последним и первым классом
            sentiment_score = float(logits[0][-1].item() - logits[0][0].item())
            sentiment_score = np.tanh(sentiment_score)
        
        # Определяем метку на основе значения
        if sentiment_score > 0.1:
            label = "positive"
        elif sentiment_score < -0.1:
            label = "negative"
        else:
            label = "neutral"
    
    return SentimentAnalysis(sentiment=sentiment_score, label=label)


def summarize_text(text: str, max_length: int = 150) -> str:
    """Суммаризация текста"""
    if summarizer_model is None or summarizer_tokenizer is None:
        raise Exception("Модель суммаризации не загружена")
    
    try:
        # Очистка текста
        text = text.strip()
        if not text:
            return "Текст для суммаризации пуст"
        
        # Токенизация с ограничением длины
        inputs = summarizer_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        print(f"🔤 Токенизировано: {inputs['input_ids'].shape[1]} токенов")
        
        # Генерация суммаризации
        with torch.no_grad():
            try:
                outputs = summarizer_model.generate(
                    **inputs,
                    max_length=max_length,
                    min_length=20,
                    num_beams=4,
                    length_penalty=2.0,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                    do_sample=False
                )
            except Exception as e:
                print(f"⚠️ Ошибка при генерации, пробую упрощенные параметры: {e}")
                # Пробуем с упрощенными параметрами
                outputs = summarizer_model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=2,
                    early_stopping=True
                )
        
        # Декодирование
        summary = summarizer_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Очистка результата
        summary = summary.strip()
        
        if not summary:
            return "Не удалось создать суммаризацию"
        
        return summary
    except Exception as e:
        print(f"❌ Ошибка в summarize_text: {e}")
        import traceback
        print(traceback.format_exc())
        raise Exception(f"Ошибка суммаризации: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Загрузка моделей и миграция БД при старте"""
    # Миграция: добавление колонок для анализа
    from sqlalchemy import text
    with engine.begin() as conn:
        try:
            # Проверяем и добавляем sentiment
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='reviews' AND column_name='sentiment'
            """))
            if not result.fetchone():
                print("🔄 Добавление колонки sentiment...")
                conn.execute(text("ALTER TABLE reviews ADD COLUMN sentiment FLOAT"))
                print("✓ Колонка sentiment добавлена")
            
            # Проверяем и добавляем sentiment_label
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='reviews' AND column_name='sentiment_label'
            """))
            if not result.fetchone():
                print("🔄 Добавление колонки sentiment_label...")
                conn.execute(text("ALTER TABLE reviews ADD COLUMN sentiment_label VARCHAR"))
                print("✓ Колонка sentiment_label добавлена")
            
            # Проверяем и добавляем summary
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='reviews' AND column_name='summary'
            """))
            if not result.fetchone():
                print("🔄 Добавление колонки summary...")
                conn.execute(text("ALTER TABLE reviews ADD COLUMN summary TEXT"))
                print("✓ Колонка summary добавлена")
        except Exception as e:
            print(f"⚠️ Миграция не выполнена (возможно колонки уже существуют): {e}")
    
    # Загрузка моделей
    try:
        print("🚀 Начало загрузки моделей...")
        load_models()
        print("✅ Все модели успешно загружены")
    except Exception as e:
        print(f"❌ Критическая ошибка при загрузке моделей: {e}")
        import traceback
        print(traceback.format_exc())
        # Не прерываем запуск, но модели не будут работать
        print("⚠️ Сервис запущен без моделей. Некоторые функции могут быть недоступны.")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "sentiment_model_loaded": sentiment_model is not None,
        "summarizer_model_loaded": summarizer_model is not None
    }


@app.post("/analytics/products/{product_id}/analyze")
async def analyze_product_reviews(
    product_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Анализ всех отзывов товара"""
    # Проверка прав доступа
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Получение отзывов без анализа
    reviews = db.query(Review).filter(
        Review.product_id == product_id,
        Review.sentiment.is_(None)
    ).all()
    
    analyzed_count = 0
    for review in reviews:
        try:
            # Анализ тональности
            sentiment_result = analyze_sentiment(review.text)
            review.sentiment = sentiment_result.sentiment
            review.sentiment_label = sentiment_result.label
            
            analyzed_count += 1
        except Exception as e:
            print(f"Ошибка анализа отзыва {review.id}: {e}")
    
    db.commit()
    
    return {
        "message": "Анализ завершен",
        "analyzed_count": analyzed_count
    }


@app.get("/analytics/products/{product_id}", response_model=AnalyticsResponse)
async def get_product_analytics(
    product_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Получение аналитики по товару"""
    # Проверка прав доступа
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Фильтр по датам
    query = db.query(Review).filter(Review.product_id == product_id)
    if start_date:
        query = query.filter(Review.date >= start_date)
    if end_date:
        query = query.filter(Review.date <= end_date)
    
    reviews = query.filter(Review.sentiment.isnot(None)).all()
    
    if not reviews:
        return AnalyticsResponse(
            product_id=product_id,
            total_reviews=0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            average_sentiment=0.0,
            timeline=[]
        )
    
    # Подсчет статистики
    total = len(reviews)
    positive_count = sum(1 for r in reviews if r.sentiment_label == "positive")
    negative_count = sum(1 for r in reviews if r.sentiment_label == "negative")
    neutral_count = sum(1 for r in reviews if r.sentiment_label == "neutral")
    average_sentiment = sum(r.sentiment for r in reviews) / total if total > 0 else 0.0
    
    # Группировка по датам для временной линии
    timeline_data = {}
    for review in reviews:
        date_key = review.date.date()
        if date_key not in timeline_data:
            timeline_data[date_key] = {"sentiments": [], "count": 0}
        timeline_data[date_key]["sentiments"].append(review.sentiment)
        timeline_data[date_key]["count"] += 1
    
    # Формирование временной линии
    timeline = []
    for date, data in sorted(timeline_data.items()):
        avg_sentiment = sum(data["sentiments"]) / len(data["sentiments"])
        timeline.append({
            "date": date.isoformat(),
            "sentiment": round(avg_sentiment, 3),
            "count": data["count"]
        })
    
    return AnalyticsResponse(
        product_id=product_id,
        total_reviews=total,
        positive_count=positive_count,
        negative_count=negative_count,
        neutral_count=neutral_count,
        average_sentiment=round(average_sentiment, 3),
        timeline=timeline
    )


@app.get("/analytics/products/{product_id}/summary", response_model=SummaryResponse)
async def get_product_summary(
    product_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Получение суммаризации всех отзывов товара"""
    import traceback
    
    try:
        # Проверка прав доступа
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.user_id == user_id
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Получение всех отзывов
        reviews = db.query(Review).filter(Review.product_id == product_id).all()
        
        if not reviews:
            raise HTTPException(status_code=404, detail="Отзывы не найдены")
        
        print(f"📊 Получено {len(reviews)} отзывов для суммаризации")
        
        # Проверка загрузки модели
        if summarizer_model is None or summarizer_tokenizer is None:
            error_msg = "Модель суммаризации не загружена"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Получаем ВСЕ тексты отзывов
        review_texts = [r.text.strip() for r in reviews if r.text and r.text.strip()]
        
        if not review_texts:
            raise HTTPException(status_code=404, detail="Нет текстов отзывов для суммаризации")
        
        print(f"📝 Всего текстов отзывов: {len(review_texts)}")
        
        # Объединяем все тексты, разделяя точками
        all_texts = ". ".join(review_texts)
        total_length = len(all_texts)
        print(f"📏 Общая длина текста: {total_length} символов")
        
        # Суммаризация всех отзывов
        # Если текст очень длинный, разбиваем на части и суммаризируем каждую
        try:
            # Максимальная длина для одной суммаризации (примерно 3000 токенов = ~2000 символов)
            MAX_CHUNK_LENGTH = 2000
            
            if total_length <= MAX_CHUNK_LENGTH:
                # Если текст помещается в один запрос - суммаризируем целиком
                print(f"📝 Суммаризация всего текста целиком...")
                summary = summarize_text(all_texts, max_length=250)
            else:
                # Если текст длинный - разбиваем на части
                print(f"📝 Текст длинный, разбиваю на части...")
                chunks = []
                current_chunk = ""
                
                for text in review_texts:
                    # Если добавление следующего текста не превысит лимит
                    if len(current_chunk) + len(text) + 2 <= MAX_CHUNK_LENGTH:
                        if current_chunk:
                            current_chunk += ". " + text
                        else:
                            current_chunk = text
                    else:
                        # Сохраняем текущий чанк и начинаем новый
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = text
                
                # Добавляем последний чанк
                if current_chunk:
                    chunks.append(current_chunk)
                
                print(f"📦 Разбито на {len(chunks)} частей")
                
                # Суммаризируем каждую часть
                chunk_summaries = []
                for i, chunk in enumerate(chunks, 1):
                    print(f"   📝 Суммаризация части {i}/{len(chunks)} ({len(chunk)} символов)...")
                    chunk_summary = summarize_text(chunk, max_length=150)
                    chunk_summaries.append(chunk_summary)
                
                # Объединяем суммаризации частей
                combined_summaries = ". ".join(chunk_summaries)
                print(f"📝 Финальная суммаризация объединенных частей ({len(combined_summaries)} символов)...")
                
                # Если объединенные суммаризации все еще длинные, суммаризируем их еще раз
                if len(combined_summaries) > MAX_CHUNK_LENGTH:
                    summary = summarize_text(combined_summaries, max_length=250)
                else:
                    summary = combined_summaries
            
            print(f"✅ Суммаризация завершена, длина результата: {len(summary)} символов")
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"❌ Ошибка при суммаризации: {e}")
            print(f"Детали: {error_details}")
            raise HTTPException(status_code=500, detail=f"Ошибка суммаризации: {str(e)}")
        
        if not summary or len(summary.strip()) == 0:
            summary = "Не удалось создать суммаризацию. Попробуйте позже."
        
        return SummaryResponse(
            product_id=product_id,
            summary=summary,
            total_reviews=len(reviews)
        )
    except HTTPException:
        raise
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"❌ Неожиданная ошибка в get_product_summary: {e}")
        print(f"Детали: {error_details}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

