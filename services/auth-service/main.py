from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from typing import Optional

app = FastAPI(
    title="Auth Service",
    redirect_slashes=False  # Отключаем автоматические редиректы
)

# Безопасность
security = HTTPBearer()

# Инициализация bcrypt с правильными настройками
try:
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        bcrypt__rounds=12
    )
except Exception as e:
    print(f"⚠ Warning: bcrypt initialization failed: {e}, using fallback")
    # Fallback на sha256, если bcrypt не работает
    pwd_context = None

# JWT настройки
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "86400"))

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_analytics")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Модели БД
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Создание таблиц будет выполнено при старте приложения


# Pydantic модели
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str


# Утилиты
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    if not pwd_context:
        # Fallback проверка
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        # Fallback проверка
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Хеширование пароля с обработкой ограничения bcrypt (72 байта)"""
    if not pwd_context:
        # Fallback на sha256, если bcrypt не работает
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    try:
        # Обрезаем пароль до 72 байт (ограничение bcrypt)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            password = password_bytes.decode('utf-8', errors='ignore')
        # Используем bytes напрямую для bcrypt
        return pwd_context.hash(password)
    except Exception as e:
        # Fallback на sha256, если bcrypt не работает
        import hashlib
        print(f"⚠ Warning: bcrypt hash failed, using sha256: {e}")
        return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


@app.on_event("startup")
async def startup_event():
    """Создание таблиц и тестового пользователя при старте приложения"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        
        # Создание тестового пользователя, если его нет
        db = SessionLocal()
        try:
            test_user = db.query(User).filter(
                (User.email == "test@test.com") | (User.username == "test")
            ).first()
            
            if not test_user:
                try:
                    test_password = "test123"
                    hashed = get_password_hash(test_password)
                    test_user = User(
                        email="test@test.com",
                        username="test",
                        hashed_password=hashed
                    )
                    db.add(test_user)
                    db.commit()
                    print("✓ Тестовый пользователь создан:")
                    print("  Email: test@test.com")
                    print("  Username: test")
                    print("  Password: test123")
                except Exception as e:
                    print(f"⚠ Warning: Could not create test user: {e}")
                    import traceback
                    print(traceback.format_exc())
                    db.rollback()
            else:
                print("✓ Тестовый пользователь уже существует")
        except Exception as e:
            print(f"⚠ Warning: Could not check/create test user: {e}")
            import traceback
            print(traceback.format_exc())
        finally:
            db.close()
    except Exception as e:
        print(f"⚠ Warning: Could not create tables: {e}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверка существующего пользователя
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email или username уже существует")
    
    # Создание нового пользователя
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Создание токена
    access_token = create_access_token(data={"sub": user_data.email, "user_id": new_user.id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=new_user.id,
        username=new_user.username
    )


@app.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Вход пользователя"""
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    # Создание токена
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )


@app.get("/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверка токена"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("sub")
        
        if user_id is None or email is None:
            raise HTTPException(status_code=401, detail="Недействительный токен")
        
        return {"user_id": user_id, "email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

