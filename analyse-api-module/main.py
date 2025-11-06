"""
Главный файл API Gateway для сервиса анализа отзывов.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем сервис анализа
# Попытка импорта из установленного пакета или относительного пути
try:
    from analyse_service import ReviewAnalyzer, AnalysisResult
except ImportError:
    # Если пакет не установлен, пробуем добавить путь
    import sys
    from pathlib import Path
    service_module_path = Path(__file__).parent.parent / "analyse-service-module"
    if service_module_path.exists():
        sys.path.insert(0, str(service_module_path))
        from analyse_service import ReviewAnalyzer, AnalysisResult
    else:
        raise ImportError(
            "Не удалось найти analyse-service-module. "
            "Установите его: cd analyse-service-module && pip install -e ."
        )

app = FastAPI(
    title="Analyse API",
    description="API для анализа отзывов о товарах",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройки безопасности
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Инициализация анализатора
analyzer = ReviewAnalyzer()


# Модели данных
class ReviewAnalysisRequest(BaseModel):
    """Запрос на анализ отзывов."""
    reviews: List[str] = Field(..., description="Список отзывов о товаре", min_items=1)
    product_id: Optional[str] = Field(None, description="ID товара (опционально)")


class ReviewAnalysisResponse(BaseModel):
    """Ответ с результатом анализа."""
    summary: str
    rating: float
    positive_aspects: List[str]
    negative_aspects: List[str]
    confidence: float
    product_id: Optional[str] = None


class User(BaseModel):
    """Модель пользователя."""
    username: str
    email: Optional[str] = None
    disabled: bool = False


class UserInDB(User):
    """Пользователь в БД с паролем."""
    hashed_password: str


class Token(BaseModel):
    """Модель токена."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Данные токена."""
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Запрос на вход."""
    username: str
    password: str


# Временная БД пользователей (в продакшене использовать реальную БД)
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),  # Пароль: admin123
        "disabled": False,
    },
    "user": {
        "username": "user",
        "email": "user@example.com",
        "hashed_password": pwd_context.hash("user123"),  # Пароль: user123
        "disabled": False,
    }
}


# Утилиты для работы с JWT
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля."""
    return pwd_context.hash(password)


def get_user(db: dict, username: str) -> Optional[UserInDB]:
    """Получение пользователя из БД."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(fake_db: dict, username: str, password: str) -> Optional[UserInDB]:
    """Аутентификация пользователя."""
    user = get_user(fake_db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Получение текущего пользователя из токена."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Получение активного пользователя."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Неактивный пользователь")
    return current_user


# Эндпоинты
@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "Analyse API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/auth/login", response_model=Token, tags=["Аутентификация"])
async def login(login_data: LoginRequest):
    """
    Вход в систему и получение JWT токена.
    
    Тестовые пользователи:
    - admin / admin123
    - user / user123
    """
    user = authenticate_user(fake_users_db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=User, tags=["Аутентификация"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе."""
    return current_user


@app.post(
    "/analyze/reviews",
    response_model=ReviewAnalysisResponse,
    tags=["Анализ отзывов"],
    summary="Анализ отзывов о товаре",
    description="Анализирует стопку отзывов и возвращает краткую выжимку, оценку и аспекты"
)
async def analyze_reviews(
    request: ReviewAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Анализ отзывов о товаре.
    
    Требует аутентификации.
    
    - **reviews**: Список отзывов для анализа
    - **product_id**: Опциональный ID товара
    
    Возвращает:
    - **summary**: Краткая выжимка на основе отзывов
    - **rating**: Оценка товара от 0 до 10
    - **positive_aspects**: Положительные аспекты
    - **negative_aspects**: Отрицательные аспекты
    - **confidence**: Уверенность в результате (0-1)
    """
    try:
        result: AnalysisResult = analyzer.analyze_reviews(request.reviews)
        
        return ReviewAnalysisResponse(
            summary=result.summary,
            rating=result.rating,
            positive_aspects=result.positive_aspects,
            negative_aspects=result.negative_aspects,
            confidence=result.confidence,
            product_id=request.product_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при анализе отзывов: {str(e)}"
        )


@app.get("/health", tags=["Система"])
async def health_check():
    """Проверка здоровья сервиса."""
    return {
        "status": "healthy",
        "service": "analyse-api",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

