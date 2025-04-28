from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Any
import torch
import numpy as np
from collections import defaultdict
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ReviewAnalyzer:
    def __init__(self):
        # Загружаем модели для разных задач
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="blanchefort/rubert-base-cased-sentiment",
            tokenizer="blanchefort/rubert-base-cased-sentiment"
        )
        
        self.summarizer = pipeline(
            "summarization",
            model="IlyaGusev/rugpt3medium_sum_gazeta",
            tokenizer="IlyaGusev/rugpt3medium_sum_gazeta"
        )
        
        self.aspect_classifier = pipeline(
            "text-classification",
            model="cointegrated/rubert-tiny2-product-aspects",
            tokenizer="cointegrated/rubert-tiny2-product-aspects"
        )
        
        logger.info("Review analyzer models loaded successfully")
    
    async def analyze_reviews(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ отзывов о товаре"""
        try:
            if not reviews:
                return {
                    "summary": "Нет отзывов для анализа",
                    "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
                    "aspects": {},
                    "quality_score": 0,
                    "recommendations": []
                }
            
            # Анализ тональности
            sentiments = self._analyze_sentiment([r["text"] for r in reviews])
            
            # Анализ аспектов
            aspects = self._analyze_aspects([r["text"] for r in reviews])
            
            # Генерация саммари
            summary = self._generate_summary(reviews)
            
            # Расчет общего качества
            quality_score = self._calculate_quality_score(reviews, sentiments, aspects)
            
            # Формируем рекомендации
            recommendations = self._generate_recommendations(aspects, sentiments)
            
            result = {
                "summary": summary,
                "sentiment": {
                    "positive": sentiments.count("positive") / len(sentiments) * 100,
                    "neutral": sentiments.count("neutral") / len(sentiments) * 100,
                    "negative": sentiments.count("negative") / len(sentiments) * 100
                },
                "aspects": aspects,
                "quality_score": quality_score,
                "recommendations": recommendations,
                "analyzed_at": datetime.now().isoformat(),
                "total_reviews": len(reviews)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing reviews: {e}")
            raise
    
    def _analyze_sentiment(self, texts: List[str]) -> List[str]:
        """Анализ тональности отзывов"""
        try:
            results = []
            for text in texts:
                sentiment = self.sentiment_analyzer(text)[0]
                label = sentiment["label"]
                score = sentiment["score"]
                
                if score < 0.4:
                    results.append("negative")
                elif score > 0.6:
                    results.append("positive")
                else:
                    results.append("neutral")
            
            return results
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return ["neutral"] * len(texts)
    
    def _analyze_aspects(self, texts: List[str]) -> Dict[str, Dict[str, float]]:
        """Анализ аспектов товара в отзывах"""
        aspects = defaultdict(lambda: {"positive": 0, "negative": 0, "mentions": 0})
        
        try:
            for text in texts:
                # Определяем аспекты в тексте
                aspect_results = self.aspect_classifier(text)
                
                for aspect in aspect_results:
                    aspect_name = aspect["label"]
                    score = aspect["score"]
                    
                    aspects[aspect_name]["mentions"] += 1
                    if score > 0.6:
                        aspects[aspect_name]["positive"] += 1
                    elif score < 0.4:
                        aspects[aspect_name]["negative"] += 1
            
            # Преобразуем счетчики в проценты
            for aspect in aspects.values():
                total = aspect["mentions"]
                if total > 0:
                    aspect["positive"] = (aspect["positive"] / total) * 100
                    aspect["negative"] = (aspect["negative"] / total) * 100
            
            return dict(aspects)
        except Exception as e:
            logger.error(f"Error in aspect analysis: {e}")
            return {}
    
    def _generate_summary(self, reviews: List[Dict[str, Any]]) -> str:
        """Генерация краткого саммари отзывов"""
        try:
            # Объединяем тексты отзывов
            combined_text = " ".join([r["text"] for r in reviews])
            
            # Генерируем саммари
            summary = self.summarizer(
                combined_text,
                max_length=150,
                min_length=50,
                do_sample=False
            )[0]["summary_text"]
            
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Не удалось сгенерировать краткое описание отзывов."
    
    def _calculate_quality_score(
        self,
        reviews: List[Dict[str, Any]],
        sentiments: List[str],
        aspects: Dict[str, Dict[str, float]]
    ) -> float:
        """Расчет общего показателя качества товара"""
        try:
            # Учитываем тональность отзывов (40% веса)
            sentiment_score = (
                (sentiments.count("positive") * 1.0 +
                 sentiments.count("neutral") * 0.5 +
                 sentiments.count("negative") * 0.0) / len(sentiments)
            ) * 0.4
            
            # Учитываем оценки пользователей (30% веса)
            ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
            rating_score = (sum(ratings) / len(ratings) / 5) * 0.3 if ratings else 0
            
            # Учитываем аспекты товара (30% веса)
            aspect_scores = []
            for aspect_data in aspects.values():
                if aspect_data["mentions"] > 0:
                    score = (aspect_data["positive"] - aspect_data["negative"]) / 100
                    aspect_scores.append(score)
            
            aspect_score = (sum(aspect_scores) / len(aspect_scores)) * 0.3 if aspect_scores else 0
            
            # Итоговая оценка
            total_score = (sentiment_score + rating_score + aspect_score) * 100
            
            return round(max(0, min(100, total_score)), 1)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def _generate_recommendations(
        self,
        aspects: Dict[str, Dict[str, float]],
        sentiments: List[str]
    ) -> List[str]:
        """Генерация рекомендаций на основе анализа"""
        recommendations = []
        
        try:
            # Общая рекомендация на основе тональности
            positive_percent = (sentiments.count("positive") / len(sentiments)) * 100
            if positive_percent >= 70:
                recommendations.append("Товар высоко оценен покупателями")
            elif positive_percent <= 30:
                recommendations.append("Товар имеет много негативных отзывов")
            
            # Рекомендации по аспектам
            for aspect_name, data in aspects.items():
                if data["mentions"] >= 3:  # Минимальное количество упоминаний
                    if data["positive"] >= 70:
                        recommendations.append(f"Высокая оценка аспекта '{aspect_name}'")
                    elif data["negative"] >= 70:
                        recommendations.append(f"Много нареканий к аспекту '{aspect_name}'")
            
            return recommendations[:5]  # Возвращаем топ-5 рекомендаций
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Недостаточно данных для формирования рекомендаций"] 