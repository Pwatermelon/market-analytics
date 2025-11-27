# Структура проекта

```
market-analytics/
├── docker-compose.yml          # Оркестрация всех сервисов
├── download_models.py          # Скрипт для скачивания ML моделей
├── requirements.txt            # Python зависимости для скачивания моделей
├── .env.example                # Пример конфигурации
├── .gitignore                  # Игнорируемые файлы
│
├── models/                     # ML модели (создается после скачивания)
│   ├── sentiment/             # Модель для тональности
│   └── summarizer/            # Модель для суммаризации
│
├── services/                   # Микросервисы
│   ├── api-gateway/           # API Gateway (порт 8000)
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── auth-service/          # Сервис авторизации (порт 8001)
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── parser-service/        # Сервис парсинга (порт 8002)
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── analyzer-service/      # Сервис анализа ML (порт 8003)
│       ├── main.py
│       ├── requirements.txt
│       └── Dockerfile
│
└── frontend/                   # React приложение (порт 3000)
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── App.js             # Главный компонент
    │   ├── App.css
    │   ├── index.js
    │   ├── index.css
    │   ├── components/        # React компоненты
    │   │   ├── Login.js
    │   │   ├── Register.js
    │   │   ├── Dashboard.js
    │   │   ├── ProductDetail.js
    │   │   └── PrivateRoute.js
    │   └── context/
    │       └── AuthContext.js  # Контекст авторизации
    ├── package.json
    ├── Dockerfile
    └── nginx.conf
```

## Описание компонентов

### Микросервисы

1. **API Gateway** (`services/api-gateway/`)
   - Единая точка входа для всех запросов
   - Проверка JWT токенов
   - Маршрутизация запросов к соответствующим сервисам

2. **Auth Service** (`services/auth-service/`)
   - Регистрация и аутентификация пользователей
   - Генерация и проверка JWT токенов
   - Управление пользователями в БД

3. **Parser Service** (`services/parser-service/`)
   - Парсинг отзывов с маркетплейсов
   - Сохранение отзывов в БД
   - Управление товарами

4. **Analyzer Service** (`services/analyzer-service/`)
   - Анализ тональности отзывов (ML)
   - Суммаризация отзывов (ML)
   - Генерация аналитики и графиков

### Frontend

- **React приложение** с компонентами:
  - Авторизация (Login/Register)
  - Дашборд со списком товаров
  - Детальная страница товара с графиками
  - Визуализация тональности (Recharts)

### База данных

PostgreSQL хранит:
- Пользователей (`users`)
- Товары (`products`)
- Отзывы (`reviews`) с результатами анализа

### Инфраструктура

- **Docker Compose** для оркестрации
- **Redis** для кеширования (опционально)
- **Nginx** для фронтенда

## Потоки данных

1. **Регистрация/Вход:**
   ```
   Frontend → API Gateway → Auth Service → PostgreSQL
   ```

2. **Добавление товара:**
   ```
   Frontend → API Gateway → Parser Service → PostgreSQL
   ```

3. **Парсинг отзывов:**
   ```
   Frontend → API Gateway → Parser Service → Маркетплейс API → PostgreSQL
   ```

4. **Анализ отзывов:**
   ```
   Frontend → API Gateway → Analyzer Service → ML Модели → PostgreSQL
   ```

5. **Получение аналитики:**
   ```
   Frontend → API Gateway → Analyzer Service → PostgreSQL → Frontend
   ```

