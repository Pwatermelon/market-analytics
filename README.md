# Market Analytics

Система анализа товаров и отзывов с популярных маркетплейсов.

## Возможности

- 🔍 Поиск товаров на маркетплейсах
  - Ozon (реализовано)
  - Wildberries (реализовано)
  - Яндекс.Маркет (реализовано)
  - GoldApple (в разработке)

- 📊 Анализ отзывов
  - Анализ тональности отзывов
  - Выделение ключевых аспектов товара
  - Генерация краткого содержания
  - Расчет показателей качества
  - Формирование рекомендаций

- 🎯 Особенности
  - Современный React интерфейс
  - FastAPI backend
  - Асинхронный парсинг с использованием Playwright
  - Анализ с использованием ML моделей
  - Docker контейнеризация
  - Параллельный поиск по нескольким маркетплейсам

## Требования

- Docker и Docker Compose
- Python 3.11+
- Node.js 18+

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/market-analytics.git
cd market-analytics
```

2. Запустите приложение с помощью Docker Compose:
```bash
docker-compose up --build
```

3. Откройте приложение:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Структура проекта

```
market-analytics/
├── api-gateway/          # API Gateway на FastAPI
│   ├── app.py           # Основной файл приложения
│   └── Dockerfile       # Dockerfile для API Gateway
├── frontend/            # React frontend
│   ├── src/            
│   │   ├── components/  # React компоненты
│   │   └── ...
│   └── Dockerfile      # Dockerfile для frontend
├── models/             # ML модели и анализаторы
│   └── review_analyzer.py
├── parsers/            # Парсеры маркетплейсов
│   ├── common/         # Общий код для парсеров
│   ├── ozon/          # Парсер Ozon
│   ├── wildberries/   # Парсер Wildberries
│   ├── yandexmarket/  # Парсер Яндекс.Маркет
│   └── goldapple/     # Парсер GoldApple (в разработке)
├── docker-compose.yml  # Docker Compose конфигурация
└── requirements.txt    # Python зависимости
```

## API Endpoints

### POST /api/parse
Поиск товаров на маркетплейсах

Request:
```json
{
  "query": "string",
  "marketplaces": ["ozon", "wildberries", "yandexmarket"]  // Опционально, по умолчанию ищет везде
}
```

### POST /api/analyze-reviews
Анализ отзывов о товаре

Request:
```json
{
  "product_url": "string",
  "marketplace": "string"  // "ozon", "wildberries" или "yandexmarket"
}
```

### GET /health
Проверка работоспособности сервиса

## Разработка

### Frontend

1. Перейдите в директорию frontend:
```bash
cd frontend
```

2. Установите зависимости:
```bash
npm install
```

3. Запустите в режиме разработки:
```bash
npm start
```

### Backend

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите API Gateway:
```bash
cd api-gateway
uvicorn app:app --reload
```

## Тестирование

В разработке

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## Лицензия

MIT 