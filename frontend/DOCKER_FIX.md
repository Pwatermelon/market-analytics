# Исправление проблем сборки фронтенда

## Проблема
Ошибка: `Cannot find module 'ajv/dist/compile/codegen'`

## Решение

Обновлены следующие файлы:

1. **Dockerfile** - обновлен до Node 20, добавлена явная установка ajv
2. **package.json** - добавлены зависимости ajv и ajv-keywords
3. **.npmrc** - настроен legacy-peer-deps

## Если проблема сохраняется

### Вариант 1: Использовать yarn вместо npm

Измените Dockerfile:
```dockerfile
FROM node:20-alpine as build
WORKDIR /app
RUN apk add --no-cache yarn
COPY package*.json ./
RUN yarn install
COPY . .
RUN yarn build
```

### Вариант 2: Обновить react-scripts

В package.json измените:
```json
"react-scripts": "5.0.2"
```

Или используйте более новую версию.

### Вариант 3: Использовать Vite (современная альтернатива)

Vite быстрее и не имеет таких проблем с зависимостями.

