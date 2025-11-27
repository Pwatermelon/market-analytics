from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Optional

app = FastAPI(
    title="Market Analytics API Gateway",
    redirect_slashes=False  # Отключаем автоматические редиректы
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL сервисов
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
PARSER_SERVICE_URL = os.getenv("PARSER_SERVICE_URL", "http://localhost:8002")
ANALYZER_SERVICE_URL = os.getenv("ANALYZER_SERVICE_URL", "http://localhost:8003")

# Исключения для авторизации
AUTH_EXCLUDED_PATHS = ["/api/auth/register", "/api/auth/login", "/docs", "/openapi.json", "/health"]


async def verify_token(request: Request):
    """Проверка JWT токена"""
    if request.url.path in AUTH_EXCLUDED_PATHS:
        return None
    
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Токен не предоставлен")
    
    token = token.split(" ")[1]
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Недействительный токен")
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Сервис авторизации недоступен")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/auth/register")
async def register(request: Request):
    """Регистрация пользователя"""
    try:
        body = await request.json()
    except:
        return JSONResponse(
            status_code=400,
            content={"detail": "Неверный формат запроса"}
        )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/register",
                json=body,
                timeout=10.0
            )
            try:
                content = response.json()
            except:
                content = {"detail": response.text or "Ошибка сервера"}
            
            return JSONResponse(
                status_code=response.status_code,
                content=content
            )
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"detail": f"Сервис авторизации недоступен: {str(e)}"}
            )


@app.post("/api/auth/login")
async def login(request: Request):
    """Вход пользователя"""
    try:
        body = await request.json()
    except:
        return JSONResponse(
            status_code=400,
            content={"detail": "Неверный формат запроса"}
        )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/login",
                json=body,
                timeout=10.0
            )
            try:
                content = response.json()
            except:
                content = {"detail": response.text or "Ошибка сервера"}
            
            return JSONResponse(
                status_code=response.status_code,
                content=content
            )
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"detail": f"Сервис авторизации недоступен: {str(e)}"}
            )


@app.api_route("/api/products", methods=["GET", "POST"])
async def products_proxy_root(request: Request, user: dict = Depends(verify_token)):
    """Проксирование запросов к сервису парсера (корневой путь)"""
    url = f"{PARSER_SERVICE_URL}/products"
    query = str(request.url.query)
    if query:
        url += f"?{query}"
    
    body = None
    if request.method == "POST":
        try:
            body = await request.json()
        except:
            body = None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                json=body,
                headers={"X-User-Id": str(user.get("user_id"))},
                timeout=30.0
            )
            try:
                content = response.json()
            except:
                content = {"detail": response.text or "Ошибка сервера"}
            
            return JSONResponse(
                status_code=response.status_code,
                content=content
            )
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"detail": f"Сервис парсера недоступен: {str(e)}"}
            )


@app.api_route("/api/products/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def products_proxy(request: Request, path: str, user: dict = Depends(verify_token)):
    """Проксирование запросов к сервису парсера"""
    # Убираем trailing slash если есть
    path = path.rstrip('/')
    url = f"{PARSER_SERVICE_URL}/products/{path}" if path else f"{PARSER_SERVICE_URL}/products"
    # Получаем query string правильно
    query = str(request.url.query)
    if query:
        url += f"?{query}"
    
    body = None
    if request.method in ["POST", "PUT"]:
        try:
            body = await request.json()
        except:
            body = None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                json=body,
                headers={"X-User-Id": str(user.get("user_id"))},
                timeout=30.0
            )
            try:
                content = response.json()
            except:
                content = {"detail": response.text or "Ошибка сервера"}
            
            return JSONResponse(
                status_code=response.status_code,
                content=content
            )
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"detail": f"Сервис парсера недоступен: {str(e)}"}
            )


@app.api_route("/api/analytics/{path:path}", methods=["GET", "POST"])
async def analytics_proxy(request: Request, path: str, user: dict = Depends(verify_token)):
    """Проксирование запросов к сервису анализа"""
    url = f"{ANALYZER_SERVICE_URL}/analytics/{path}"
    # Получаем query string правильно
    query = str(request.url.query)
    if query:
        url += f"?{query}"
    
    body = None
    if request.method == "POST":
        try:
            body = await request.json()
        except:
            body = None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                json=body,
                headers={"X-User-Id": str(user.get("user_id"))},
                timeout=60.0
            )
            try:
                content = response.json()
            except:
                content = {"detail": response.text or "Ошибка сервера"}
            
            return JSONResponse(
                status_code=response.status_code,
                content=content
            )
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=503,
                content={"detail": f"Сервис анализа недоступен: {str(e)}"}
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

