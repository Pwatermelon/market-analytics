"""
Модуль для анализа отзывов о товарах с использованием нейронной сети.
"""
import os
from typing import List, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import numpy as np
from pydantic import BaseModel


class AnalysisResult(BaseModel):
    """Результат анализа отзывов."""
    summary: str
    rating: float
    positive_aspects: List[str]
    negative_aspects: List[str]
    confidence: float


class ReviewAnalyzer:
    """
    Анализатор отзывов на основе нейронной сети.
    Использует предобученные модели для анализа тональности и генерации выжимок.
    """
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        Инициализация анализатора.
        
        Args:
            model_name: Название модели (по умолчанию использует русскоязычную модель)
            device: Устройство для вычислений ('cuda', 'cpu' или None для автоопределения)
        """
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Модель для анализа тональности (русскоязычная)
        self.sentiment_model_name = model_name or 'cointegrated/rubert-tiny2-cedr-emotion-detection'
        
        # Модель для суммаризации (можно заменить на обученную)
        self.summarization_model_name = 'IlyaGusev/rut5_base_sum_gazeta'
        
        print(f"Загрузка моделей на устройство: {self.device}")
        self._load_models()
    
    def _load_models(self):
        """Загрузка моделей для анализа."""
        try:
            # Модель для анализа тональности
            self.sentiment_tokenizer = AutoTokenizer.from_pretrained(self.sentiment_model_name)
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
                self.sentiment_model_name
            ).to(self.device)
            self.sentiment_model.eval()
            
            # Pipeline для суммаризации
            self.summarizer = pipeline(
                "summarization",
                model=self.summarization_model_name,
                tokenizer=self.summarization_model_name,
                device=0 if self.device == 'cuda' else -1
            )
            
            print("Модели успешно загружены")
        except Exception as e:
            print(f"Ошибка при загрузке моделей: {e}")
            print("Используется упрощенный режим анализа")
            self.sentiment_model = None
            self.summarizer = None
    
    def _analyze_sentiment(self, text: str) -> tuple[float, float]:
        """
        Анализ тональности текста.
        
        Returns:
            (positive_score, negative_score)
        """
        if self.sentiment_model is None:
            # Упрощенный анализ без модели
            positive_words = ['хороший', 'отличный', 'качественный', 'рекомендую', 'доволен']
            negative_words = ['плохой', 'некачественный', 'разочарован', 'не рекомендую', 'брак']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            total = positive_count + negative_count
            if total == 0:
                return 0.5, 0.5
            
            return positive_count / total, negative_count / total
        
        try:
            inputs = self.sentiment_tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.sentiment_model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
            
            # Предполагаем, что последний класс - позитивный
            positive_score = float(probs[-1]) if len(probs) > 1 else 0.5
            negative_score = 1.0 - positive_score
            
            return positive_score, negative_score
        except Exception as e:
            print(f"Ошибка анализа тональности: {e}")
            return 0.5, 0.5
    
    def _generate_summary(self, reviews: List[str]) -> str:
        """
        Генерация краткой выжимки из отзывов.
        
        Args:
            reviews: Список отзывов
            
        Returns:
            Краткая выжимка
        """
        if not reviews:
            return "Нет отзывов для анализа"
        
        # Объединяем все отзывы
        combined_text = " ".join(reviews)
        
        # Ограничиваем длину для модели
        max_length = 1024
        if len(combined_text) > max_length:
            combined_text = combined_text[:max_length]
        
        if self.summarizer is None:
            # Упрощенная выжимка без модели
            sentences = combined_text.split('.')
            return '. '.join(sentences[:3]) + '.'
        
        try:
            summary = self.summarizer(
                combined_text,
                max_length=150,
                min_length=50,
                do_sample=False
            )
            return summary[0]['summary_text'] if isinstance(summary, list) else summary
        except Exception as e:
            print(f"Ошибка генерации выжимки: {e}")
            # Fallback на упрощенную версию
            sentences = combined_text.split('.')
            return '. '.join(sentences[:3]) + '.'
    
    def _extract_aspects(self, reviews: List[str], positive_scores: List[float]) -> tuple[List[str], List[str]]:
        """
        Извлечение положительных и отрицательных аспектов.
        
        Args:
            reviews: Список отзывов
            positive_scores: Список положительных оценок для каждого отзыва
            
        Returns:
            (positive_aspects, negative_aspects)
        """
        positive_aspects = []
        negative_aspects = []
        
        # Простое извлечение на основе тональности
        for review, score in zip(reviews, positive_scores):
            if score > 0.6:
                # Извлекаем ключевые фразы из положительных отзывов
                sentences = review.split('.')
                for sentence in sentences[:2]:  # Берем первые 2 предложения
                    if len(sentence.strip()) > 10:
                        positive_aspects.append(sentence.strip()[:100])
            elif score < 0.4:
                sentences = review.split('.')
                for sentence in sentences[:2]:
                    if len(sentence.strip()) > 10:
                        negative_aspects.append(sentence.strip()[:100])
        
        # Убираем дубликаты и ограничиваем количество
        positive_aspects = list(set(positive_aspects))[:5]
        negative_aspects = list(set(negative_aspects))[:5]
        
        return positive_aspects, negative_aspects
    
    def analyze_reviews(self, reviews: List[str]) -> AnalysisResult:
        """
        Анализ стопки отзывов.
        
        Args:
            reviews: Список отзывов о товаре
            
        Returns:
            AnalysisResult с выжимкой, оценкой и аспектами
        """
        if not reviews:
            return AnalysisResult(
                summary="Нет отзывов для анализа",
                rating=5.0,
                positive_aspects=[],
                negative_aspects=[],
                confidence=0.0
            )
        
        # Анализируем тональность каждого отзыва
        sentiment_scores = []
        for review in reviews:
            pos_score, neg_score = self._analyze_sentiment(review)
            sentiment_scores.append(pos_score)
        
        # Вычисляем общую оценку (0-10)
        avg_positive = np.mean(sentiment_scores)
        rating = avg_positive * 10.0
        
        # Генерируем выжимку
        summary = self._generate_summary(reviews)
        
        # Извлекаем аспекты
        positive_aspects, negative_aspects = self._extract_aspects(reviews, sentiment_scores)
        
        # Вычисляем уверенность (на основе согласованности оценок)
        confidence = 1.0 - np.std(sentiment_scores) if len(sentiment_scores) > 1 else 0.5
        
        return AnalysisResult(
            summary=summary,
            rating=round(rating, 2),
            positive_aspects=positive_aspects,
            negative_aspects=negative_aspects,
            confidence=round(confidence, 2)
        )

