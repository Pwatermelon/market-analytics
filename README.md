# Market Analytics

Сервис для анализа товаров с различных маркетплейсов (Ozon, Wildberries, Золотое яблоко).

## Структура проекта

- `api-gateway/` - API Gateway сервис
- `parsers/` - Микросервисы для парсинга каждого маркетплейса
  - `ozon/` - Парсер Ozon
  - `wildberries/` - Парсер Wildberries
  - `goldapple/` - Парсер Золотое яблоко
- `frontend/` - React фронтенд приложение

## Требования

- Docker
- Docker Compose

## Запуск проекта

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd market-analytics
```

2. Запустите все сервисы через Docker Compose:
```bash
docker-compose up --build
```

3. Откройте приложение в браузере:
```
http://localhost:3000
```

## API Endpoints

### API Gateway (порт 8000)
- POST `/search` - Поиск товаров
  ```json
  {
    "query": "название товара",
    "marketplace": "ozon" // опционально
  }
  ```

### Парсеры
- Ozon (порт 8001)
- Wildberries (порт 8002)
- Золотое яблоко (порт 8003)

## Разработка

### Добавление нового парсера

1. Создайте новую директорию в `parsers/`
2. Скопируйте структуру из существующего парсера
3. Реализуйте логику парсинга
4. Добавьте сервис в `docker-compose.yml`

### Локальная разработка

1. Запустите только нужные сервисы:
```bash
docker-compose up api-gateway ozon-parser
```

2. Для разработки фронтенда:
```bash
cd frontend
npm install
npm start
``` 