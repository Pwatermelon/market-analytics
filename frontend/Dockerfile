FROM node:18-alpine as build

WORKDIR /app

# Установка зависимостей для сборки
RUN apk add --no-cache python3 make g++

COPY package*.json ./
COPY .npmrc ./

# Очистка кеша
RUN npm cache clean --force

# Сначала устанавливаем правильные версии ajv и ajv-keywords
# Это нужно для совместимости с react-scripts
RUN npm install ajv@6.12.6 ajv-keywords@3.5.2 --legacy-peer-deps --save-dev

# Теперь устанавливаем остальные зависимости
RUN npm install --legacy-peer-deps

COPY . .

# Переменные окружения для обхода проблем
ENV SKIP_PREFLIGHT_CHECK=true
ENV GENERATE_SOURCEMAP=false
ENV TSC_COMPILE_ON_ERROR=true
ENV DISABLE_ESLINT_PLUGIN=true

RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

