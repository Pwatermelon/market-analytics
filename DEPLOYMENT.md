# Инструкция по развертыванию

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- 4 GB свободной оперативной памяти
- 5 GB свободного места на диске (для моделей и образов)

## Процесс развертывания

### 1. Подготовка моделей

**Важно:** Модели должны быть скачаны ДО запуска Docker контейнеров.

```bash
# Установка зависимостей для скачивания моделей
pip install -r requirements.txt

# Скачивание моделей (займет ~10-15 минут)
python download_models.py
```

Проверьте, что модели скачаны:
```bash
ls -la models/sentiment/
ls -la models/summarizer/
```

### 2. Настройка окружения (опционально)

Создайте файл `.env` в корне проекта для переопределения настроек:

```env
# JWT настройки
JWT_SECRET=your-super-secret-key-change-this
JWT_EXPIRATION=86400

# База данных
POSTGRES_PASSWORD=your-secure-password

# API URLs (для продакшена)
AUTH_SERVICE_URL=http://auth-service:8001
PARSER_SERVICE_URL=http://parser-service:8002
ANALYZER_SERVICE_URL=http://analyzer-service:8003
```

### 3. Запуск приложения

```bash
# Сборка и запуск всех сервисов
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### 4. Проверка работоспособности

```bash
# Проверка здоровья сервисов
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## Продакшен развертывание

### Рекомендации

1. **Безопасность:**
   - Измените все пароли и секретные ключи
   - Используйте HTTPS (настройте reverse proxy)
   - Ограничьте доступ к портам БД

2. **Масштабирование:**
   - Используйте внешнюю БД (RDS, Cloud SQL)
   - Настройте Redis кластер для кеширования
   - Используйте load balancer для API Gateway

3. **Мониторинг:**
   - Настройте логирование (ELK, Loki)
   - Добавьте метрики (Prometheus, Grafana)
   - Настройте алерты

4. **Резервное копирование:**
   - Настройте автоматический бэкап БД
   - Сохраняйте модели в S3/объектное хранилище

### Пример конфигурации для продакшена

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api-gateway:
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 512M

  analyzer-service:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## Обновление приложения

```bash
# Остановка
docker-compose down

# Обновление кода
git pull

# Пересборка и запуск
docker-compose up --build -d
```

## Устранение неполадок

### Проблема: Контейнеры не запускаются

```bash
# Проверьте логи
docker-compose logs

# Проверьте использование ресурсов
docker stats

# Пересоздайте контейнеры
docker-compose down -v
docker-compose up --build
```

### Проблема: Модели не загружаются

```bash
# Проверьте монтирование volume
docker-compose exec analyzer-service ls -la /app/models

# Проверьте права доступа
chmod -R 755 models/
```

### Проблема: База данных не подключается

```bash
# Проверьте статус БД
docker-compose ps postgres

# Проверьте логи БД
docker-compose logs postgres

# Пересоздайте БД (ВНИМАНИЕ: удалит все данные)
docker-compose down -v
docker volume rm market-analytics_postgres_data
docker-compose up -d postgres
```

## Мониторинг и логи

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f analyzer-service

# Статистика использования ресурсов
docker stats

# Проверка состояния контейнеров
docker-compose ps
```

## Масштабирование

Для увеличения производительности можно запустить несколько экземпляров сервисов:

```bash
# Запуск нескольких экземпляров analyzer-service
docker-compose up -d --scale analyzer-service=3
```

## Очистка

```bash
# Остановка и удаление контейнеров
docker-compose down

# Удаление контейнеров, volumes и сетей
docker-compose down -v

# Очистка неиспользуемых образов
docker system prune -a
```

