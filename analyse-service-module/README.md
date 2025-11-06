# Analyse Service Module

Сервис для анализа отзывов о товарах с использованием нейронной сети.

## Возможности

- Анализ стопки отзывов о товаре
- Генерация краткой выжимки на основе отзывов
- Определение оценки качества товара (0-10)
- Поддержка обучения собственной модели

## Установка

```bash
pip install -r requirements.txt
```

## Использование

```python
from analyse_service import ReviewAnalyzer

analyzer = ReviewAnalyzer()
result = analyzer.analyze_reviews(reviews=["отзыв 1", "отзыв 2", ...])
print(result.summary)
print(result.rating)
```

