# Инструкция по установке и запуску

## Предварительные требования

- Python 3.8 или выше
- pip
- (Опционально) CUDA для GPU ускорения

## Установка

### 1. Установка analyse-service-module

```bash
cd analyse-service-module
pip install -r requirements.txt

# Или установка как пакет (рекомендуется)
pip install -e .
```

### 2. Установка analyse-api-module

```bash
cd ../analyse-api-module
pip install -r requirements.txt

# Или установка как пакет (рекомендуется)
pip install -e .
```

### 3. Настройка переменных окружения

Создайте файл `.env` в папке `analyse-api-module`:

```bash
cd analyse-api-module
cp .env.example .env
```

Отредактируйте `.env` и установите `SECRET_KEY` (минимум 32 символа):

```
SECRET_KEY=your-very-secret-key-minimum-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Запуск

### Запуск API сервера

```bash
cd analyse-api-module
python run.py
```

Или через uvicorn напрямую:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API будет доступен по адресу: http://localhost:8000

### Тестирование

1. Откройте Swagger UI: http://localhost:8000/docs

2. Получите токен:
   - Перейдите в раздел "Аутентификация" → `/auth/login`
   - Используйте тестовые данные: `admin` / `admin123`
   - Скопируйте полученный токен

3. Протестируйте анализ отзывов:
   - Перейдите в раздел "Анализ отзывов" → `/analyze/reviews`
   - Нажмите "Authorize" и вставьте токен
   - Отправьте запрос с тестовыми отзывами

### Пример использования через Python

```bash
cd analyse-api-module
python example_usage.py
```

## Структура проекта

```
market-analytics/
├── analyse-service-module/      # Сервис анализа отзывов
│   ├── analyse_service/         # Основной модуль
│   │   ├── __init__.py
│   │   ├── analyzer.py          # Класс ReviewAnalyzer
│   │   └── config.py            # Конфигурация
│   ├── requirements.txt
│   ├── setup.py
│   └── example_usage.py
│
├── analyse-api-module/          # API Gateway
│   ├── main.py                  # FastAPI приложение
│   ├── run.py                   # Скрипт запуска
│   ├── requirements.txt
│   ├── setup.py
│   └── example_usage.py
│
└── README.md
```

## Решение проблем

### Ошибка импорта analyse_service

Если API модуль не может найти analyse_service:

1. Убедитесь, что оба модуля установлены:
   ```bash
   cd analyse-service-module
   pip install -e .
   
   cd ../analyse-api-module
   pip install -e .
   ```

2. Или убедитесь, что папки находятся на одном уровне в структуре проекта

### Ошибки загрузки моделей

При первом запуске модели будут загружены из Hugging Face. Это может занять время и требует интернет-соединения.

Если модели не загружаются, сервис переключится на упрощенный режим анализа.

### Проблемы с GPU

Если у вас есть NVIDIA GPU и вы хотите использовать CUDA:

1. Установите PyTorch с поддержкой CUDA
2. Убедитесь, что CUDA доступна: `python -c "import torch; print(torch.cuda.is_available())"`

## Следующие шаги

- Настройте базу данных для хранения пользователей
- Обучите собственную модель на ваших данных
- Настройте логирование
- Добавьте мониторинг и метрики

