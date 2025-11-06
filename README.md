# Market Analytics

Система анализа отзывов о товарах с использованием нейронных сетей.

## Структура проекта

- **analyse-service-module** - Сервис анализа отзывов с ML моделью
- **analyse-api-module** - API Gateway с аутентификацией и Swagger

## Быстрый старт

### 1. Установка зависимостей

```bash
# Установка зависимостей для сервиса анализа
cd analyse-service-module
pip install -r requirements.txt

# Установка зависимостей для API
cd ../analyse-api-module
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```bash
# В analyse-api-module создайте .env файл
cd analyse-api-module
cp .env.example .env
# Отредактируйте SECRET_KEY в .env
```

### 3. Запуск API сервера

```bash
cd analyse-api-module
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступен по адресу: http://localhost:8000

## Документация API

После запуска сервера:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Аутентификация

API использует JWT токены. Тестовые пользователи:
- **admin** / **admin123**
- **user** / **user123**

Для получения токена используйте эндпоинт `/auth/login`.

## Примеры использования

См. файлы `example_usage.py` в каждом модуле.

## Разработка

### analyse-service-module

Сервис анализа использует предобученные модели:
- Для анализа тональности: `cointegrated/rubert-tiny2-cedr-emotion-detection`
- Для суммаризации: `IlyaGusev/rut5_base_sum_gazeta`

Модели можно заменить на собственные, обучив их на ваших данных.

### analyse-api-module

API Gateway построен на FastAPI с:
- Автоматической Swagger документацией
- JWT аутентификацией
- Защищенными эндпоинтами
- CORS поддержкой

## Следующие шаги

- [ ] Telegram бот
- [ ] Frontend на React.js
- [ ] Обучение собственной модели
- [ ] Интеграция с базой данных

