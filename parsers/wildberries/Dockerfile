FROM python:3.11-slim

WORKDIR /app

# Настройка DNS
RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf && \
    echo "nameserver 8.8.4.4" >> /etc/resolv.conf

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости
COPY wildberries/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка Playwright и его зависимостей
RUN playwright install chromium
RUN playwright install-deps

# Копируем код парсера
COPY wildberries/ ./wildberries/
COPY common/ ./common/

ENV PYTHONPATH=/app

CMD ["python", "wildberries/main.py"] 