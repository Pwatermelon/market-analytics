"""
Конфигурация для сервиса анализа.
"""
import os
from typing import Optional


class Config:
    """Настройки сервиса."""
    
    # Модели
    SENTIMENT_MODEL: str = os.getenv(
        'SENTIMENT_MODEL',
        'cointegrated/rubert-tiny2-cedr-emotion-detection'
    )
    SUMMARIZATION_MODEL: str = os.getenv(
        'SUMMARIZATION_MODEL',
        'IlyaGusev/rut5_base_sum_gazeta'
    )
    
    # Устройство для вычислений
    DEVICE: Optional[str] = os.getenv('DEVICE', None)  # 'cuda' или 'cpu'
    
    # Логирование
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

