# Analyse API Module

API Gateway для сервиса анализа отзывов.

## Возможности

- RESTful API для анализа отзывов
- Swagger документация (автоматически)
- JWT аутентификация
- Защищенные эндпоинты
- Интеграция с analyse-service-module

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Документация API

После запуска доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Аутентификация

API использует JWT токены. Для получения токена используйте эндпоинт `/auth/login`.

