FROM python:3.11-slim

WORKDIR /app

# Установка минимальных системных зависимостей
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка Chrome через Playwright (самый надежный способ)
# Playwright сам установит все зависимости для Chrome
RUN playwright install chromium && \
    playwright install-deps chromium || true

COPY . .

# Переменные окружения для headless режима
ENV DISPLAY=:99
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
