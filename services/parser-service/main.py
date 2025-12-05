from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import os
import re
from typing import Optional, List
import httpx
import logging
import sys
try:
    from parsers.simple_parsers import SimpleWildberriesParser, SimpleOzonParser, SimpleYandexMarketParser
    # Fallback на старые парсеры
    try:
        from parsers.wildberries_parser import WildberriesParser
    except:
        WildberriesParser = None
    try:
        from parsers.ozon_parser import OzonParser
    except:
        OzonParser = None
    try:
        from parsers.yandex_market_parser import YandexMarketParser
    except:
        YandexMarketParser = None
except ImportError:
    SimpleWildberriesParser = None
    SimpleOzonParser = None
    SimpleYandexMarketParser = None
    WildberriesParser = None
    OzonParser = None
    YandexMarketParser = None

app = FastAPI(
    title="Parser Service",
    redirect_slashes=False  # Отключаем автоматические редиректы
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_analytics")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Модели БД
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    marketplace = Column(String, nullable=False)  # wildberries, ozon, yandex-market и т.д.
    parsing_status = Column(String, default="idle")  # idle, parsing, completed, error
    last_parsed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    author = Column(String)
    rating = Column(Integer)
    text = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="reviews")


# Создание таблиц будет выполнено при старте приложения


# Pydantic модели
class ProductCreate(BaseModel):
    name: str
    url: HttpUrl
    marketplace: str


class ProductResponse(BaseModel):
    id: int
    name: str
    url: str
    marketplace: str
    parsing_status: Optional[str] = "idle"
    last_parsed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    id: int
    author: Optional[str]
    rating: Optional[int]
    text: str
    date: datetime
    
    class Config:
        from_attributes = True


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


def detect_marketplace(url: str) -> str:
    """Определение маркетплейса по URL"""
    url_lower = url.lower()
    if "wildberries.ru" in url_lower or "wb.ru" in url_lower:
        return "wildberries"
    elif "ozon.ru" in url_lower or "ozon.com" in url_lower:
        return "ozon"
    elif "yandex.ru/market" in url_lower or "market.yandex.ru" in url_lower or "yandex.ru/market" in url_lower:
        return "yandex-market"
    elif "aliexpress.ru" in url_lower or "aliexpress.com" in url_lower:
        return "aliexpress"
    else:
        return "unknown"


def parse_reviews(url: str, marketplace: str) -> List[dict]:
    """Парсинг отзывов в зависимости от маркетплейса"""
    logger.info(f"🌐 Запуск парсера для {marketplace}: {url}")
    try:
        if marketplace == "wildberries":
            # Используем простой парсер
            if SimpleWildberriesParser:
                try:
                    logger.info("🔧 Инициализация простого парсера Wildberries...")
                    parser = SimpleWildberriesParser()
                    logger.info("📥 Начало парсинга отзывов...")
                    reviews = parser.parse_reviews(str(url))
                    logger.info(f"✅ Парсинг завершен, получено отзывов: {len(reviews)}")
                    return reviews
                except Exception as e:
                    logger.warning(f"⚠️ Простой парсер не сработал: {e}")
            
            # Fallback на старый парсер
            if WildberriesParser:
                logger.info("🔧 Инициализация парсера Wildberries (fallback)...")
                parser = WildberriesParser()
            else:
                logger.error("❌ Парсер Wildberries не доступен")
                raise HTTPException(status_code=500, detail="Парсер Wildberries не доступен")
            try:
                logger.info("📥 Начало парсинга отзывов...")
                reviews = parser.parse_reviews(str(url))
                logger.info(f"✅ Парсинг завершен, получено отзывов: {len(reviews) if reviews else 0}")
                return reviews
            finally:
                # Закрываем браузер в любом случае
                if parser and parser.driver:
                    try:
                        logger.info("🔒 Закрытие браузера...")
                        parser.driver.quit()
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при закрытии браузера: {e}")
        elif marketplace == "ozon":
            # Используем простой парсер
            if SimpleOzonParser:
                try:
                    logger.info("🔧 Инициализация простого парсера Ozon...")
                    parser = SimpleOzonParser()
                    logger.info("📥 Начало парсинга отзывов...")
                    reviews = parser.parse_reviews(str(url))
                    logger.info(f"✅ Парсинг завершен, получено отзывов: {len(reviews)}")
                    return reviews
                except Exception as e:
                    logger.warning(f"⚠️ Простой парсер не сработал: {e}")
            
            # Fallback на старый парсер
            if OzonParser:
                logger.info("🔧 Инициализация парсера Ozon (fallback)...")
                parser = OzonParser()
            else:
                logger.error("❌ Парсер Ozon не доступен")
                raise HTTPException(status_code=500, detail="Парсер Ozon не доступен")
            try:
                logger.info("📥 Начало парсинга отзывов...")
                reviews = parser.parse_reviews(str(url))
                logger.info(f"✅ Парсинг завершен, получено отзывов: {len(reviews) if reviews else 0}")
                return reviews
            finally:
                # Закрываем браузер в любом случае
                if parser and parser.driver:
                    try:
                        logger.info("🔒 Закрытие браузера...")
                        parser.driver.quit()
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при закрытии браузера: {e}")
        elif marketplace == "yandex-market":
            # Используем простой парсер
            if SimpleYandexMarketParser:
                try:
                    logger.info("🔧 Инициализация простого парсера Яндекс.Маркет...")
                    parser = SimpleYandexMarketParser()
                    logger.info("📥 Начало парсинга отзывов...")
                    reviews = parser.parse_reviews(str(url))
                    logger.info(f"✅ Парсинг завершен, получено отзывов: {len(reviews)}")
                    return reviews
                except Exception as e:
                    logger.warning(f"⚠️ Простой парсер не сработал: {e}")
            
            # Fallback на старый парсер
            if YandexMarketParser:
                logger.info("🔧 Инициализация парсера Яндекс.Маркет (fallback)...")
                parser = YandexMarketParser()
            else:
                logger.error("❌ Парсер Яндекс.Маркет не доступен")
                raise HTTPException(status_code=500, detail="Парсер Яндекс.Маркет не доступен")
            try:
                logger.info("📥 Начало парсинга отзывов...")
                reviews = parser.parse_reviews(str(url))
                logger.info(f"✅ Парсинг завершен, получено отзывов: {len(reviews) if reviews else 0}")
                return reviews
            finally:
                # Закрываем браузер в любом случае
                if parser and parser.driver:
                    try:
                        logger.info("🔒 Закрытие браузера...")
                        parser.driver.quit()
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при закрытии браузера: {e}")
        else:
            logger.error(f"❌ Неподдерживаемый маркетплейс: {marketplace}")
            raise HTTPException(status_code=400, detail=f"Парсинг для маркетплейса {marketplace} пока не реализован")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"❌ Ошибка парсинга {marketplace}: {error_details}")
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Создание таблиц и миграции при старте приложения"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully")
        
        # Добавляем новые колонки, если их нет (миграция)
        from sqlalchemy import text
        with engine.begin() as conn:
            try:
                # Проверяем и добавляем parsing_status
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='products' AND column_name='parsing_status'
                """))
                if not result.fetchone():
                    logger.info("🔄 Добавление колонки parsing_status...")
                    conn.execute(text("ALTER TABLE products ADD COLUMN parsing_status VARCHAR DEFAULT 'idle'"))
                    logger.info("✓ Колонка parsing_status добавлена")
                
                # Проверяем и добавляем last_parsed_at
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='products' AND column_name='last_parsed_at'
                """))
                if not result.fetchone():
                    logger.info("🔄 Добавление колонки last_parsed_at...")
                    conn.execute(text("ALTER TABLE products ADD COLUMN last_parsed_at TIMESTAMP"))
                    logger.info("✓ Колонка last_parsed_at добавлена")
            except Exception as e:
                logger.warning(f"⚠️ Миграция не выполнена (возможно колонки уже существуют): {e}")
        
        # Инициализация тестовых данных
        try:
            from init_test_data import init_test_data
            logger.info("🚀 Инициализация тестовых данных...")
            init_test_data()
            logger.info("✅ Тестовые данные инициализированы")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось инициализировать тестовые данные: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    except Exception as e:
        logger.error(f"⚠ Warning: Could not create tables: {e}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Создание нового товара для отслеживания"""
    url_str = str(product.url)
    marketplace = product.marketplace or detect_marketplace(url_str)
    
    # Проверка существующего товара
    existing = db.query(Product).filter(Product.url == url_str).first()
    if existing:
        raise HTTPException(status_code=400, detail="Товар с таким URL уже существует")
    
    new_product = Product(
        user_id=user_id,
        name=product.name,
        url=url_str,
        marketplace=marketplace
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return ProductResponse.model_validate(new_product)


@app.get("/products", response_model=List[ProductResponse])
async def get_products(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Получение списка товаров пользователя"""
    products = db.query(Product).filter(Product.user_id == user_id).all()
    return [ProductResponse.model_validate(p) for p in products]


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Получение товара по ID"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return ProductResponse.model_validate(product)


@app.post("/products/{product_id}/parse")
async def parse_product_reviews(
    product_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Запуск парсинга отзывов для товара"""
    logger.info(f"🚀 Начало парсинга товара ID={product_id} для пользователя ID={user_id}")
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()
    
    if not product:
        logger.warning(f"❌ Товар ID={product_id} не найден")
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Устанавливаем статус "parsing"
    product.parsing_status = "parsing"
    db.commit()
    logger.info(f"📦 Товар: {product.name} | URL: {product.url} | Маркетплейс: {product.marketplace}")
    
    # Парсинг отзывов
    try:
        # Получаем название товара, если не указано
        if not product.name or product.name == "":
            logger.info("🔍 Получение названия товара...")
            try:
                parser = None
                if product.marketplace == "wildberries" and WildberriesParser:
                    logger.info("🌐 Используется парсер Wildberries")
                    parser = WildberriesParser()
                    product.name = parser.get_product_name(product.url) or product.name
                elif product.marketplace == "ozon":
                    if SimpleOzonParser:
                        try:
                            parser = SimpleOzonParser()
                            product.name = parser.get_product_name(product.url) or product.name
                        except:
                            if OzonParser:
                                parser = OzonParser()
                                product.name = parser.get_product_name(product.url) or product.name
                    elif OzonParser:
                        parser = OzonParser()
                        product.name = parser.get_product_name(product.url) or product.name
                elif product.marketplace == "yandex-market":
                    if SimpleYandexMarketParser:
                        try:
                            parser = SimpleYandexMarketParser()
                            product.name = parser.get_product_name(product.url) or product.name
                        except:
                            if YandexMarketParser:
                                parser = YandexMarketParser()
                                product.name = parser.get_product_name(product.url) or product.name
                    elif YandexMarketParser:
                        parser = YandexMarketParser()
                        product.name = parser.get_product_name(product.url) or product.name
                
                if parser and parser.driver:
                    try:
                        parser.driver.quit()
                    except:
                        pass
                
                if product.name:
                    db.commit()
                    logger.info(f"✅ Название товара получено: {product.name}")
            except Exception as e:
                logger.error(f"⚠️ Не удалось получить название товара: {e}")
        
        # Парсинг отзывов (запускаем в отдельном потоке, чтобы не блокировать event loop)
        logger.info(f"🔎 Начало парсинга отзывов с {product.marketplace}...")
        import asyncio
        loop = asyncio.get_event_loop()
        reviews_data = await loop.run_in_executor(None, parse_reviews, product.url, product.marketplace)
        
        if not reviews_data:
            product.parsing_status = "completed"
            product.last_parsed_at = datetime.utcnow()
            db.commit()
            logger.warning(f"⚠️ Отзывы не найдены для товара ID={product_id}")
            return {
                "message": "Отзывы не найдены или не удалось их получить",
                "parsed_count": 0,
                "new_reviews": 0,
                "status": "completed"
            }
        
        logger.info(f"📊 Найдено отзывов: {len(reviews_data)}")
        
        # Сохранение отзывов в БД
        logger.info("💾 Сохранение отзывов в базу данных...")
        new_reviews = []
        duplicates = 0
        for i, review_data in enumerate(reviews_data, 1):
            # Проверка на дубликаты (по тексту и дате)
            existing = db.query(Review).filter(
                Review.product_id == product_id,
                Review.text == review_data["text"],
                Review.date == review_data["date"]
            ).first()
            
            if not existing:
                review = Review(
                    product_id=product_id,
                    author=review_data.get("author"),
                    rating=review_data.get("rating"),
                    text=review_data["text"],
                    date=review_data["date"]
                )
                new_reviews.append(review)
            else:
                duplicates += 1
            
            if i % 10 == 0:
                logger.info(f"  Обработано: {i}/{len(reviews_data)} отзывов")
        
        db.add_all(new_reviews)
        product.parsing_status = "completed"
        product.last_parsed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Парсинг завершен успешно!")
        logger.info(f"   📈 Всего отзывов: {len(reviews_data)}")
        logger.info(f"   ✨ Новых отзывов: {len(new_reviews)}")
        logger.info(f"   🔄 Дубликатов пропущено: {duplicates}")
        
        return {
            "message": "Парсинг завершен успешно",
            "parsed_count": len(reviews_data),
            "new_reviews": len(new_reviews),
            "duplicates_skipped": duplicates,
            "status": "completed"
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"❌ Ошибка при парсинге: {error_details}")
        product.parsing_status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Ошибка при парсинге: {str(e)}")


@app.get("/products/{product_id}/status")
async def get_parsing_status(
    product_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Получение статуса парсинга товара"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    reviews_count = db.query(Review).filter(Review.product_id == product_id).count()
    
    return {
        "product_id": product_id,
        "status": product.parsing_status or "idle",
        "last_parsed_at": product.last_parsed_at.isoformat() if product.last_parsed_at else None,
        "reviews_count": reviews_count
    }


@app.get("/products/{product_id}/reviews", response_model=List[ReviewResponse])
async def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Получение отзывов товара"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    reviews = db.query(Review).filter(Review.product_id == product_id).order_by(Review.date.desc()).all()
    return [ReviewResponse.model_validate(r) for r in reviews]


@app.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id)
):
    """Удаление товара и всех его отзывов"""
    logger.info(f"🗑️ Удаление товара ID={product_id} пользователем ID={user_id}")
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()
    
    if not product:
        logger.warning(f"❌ Товар ID={product_id} не найден")
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    try:
        # Подсчитываем отзывы перед удалением
        reviews_count = db.query(Review).filter(Review.product_id == product_id).count()
        
        # Удаляем товар (отзывы удалятся автоматически благодаря cascade)
        db.delete(product)
        db.commit()
        
        logger.info(f"✅ Товар '{product.name}' удален вместе с {reviews_count} отзывами")
        
        return {
            "message": "Товар успешно удален",
            "deleted_product_id": product_id,
            "deleted_reviews_count": reviews_count
        }
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении товара: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении товара: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

