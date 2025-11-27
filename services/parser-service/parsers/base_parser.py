"""
Базовый класс для парсеров маркетплейсов
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import time
import random
from fake_useragent import UserAgent
import cloudscraper


class BaseParser(ABC):
    """Базовый класс для всех парсеров"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.session = self.scraper
        self._setup_session()
    
    def _setup_session(self):
        """Настройка сессии с обходом блокировок"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Случайная задержка для имитации человеческого поведения"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _get_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Получение страницы с повторными попытками"""
        for attempt in range(retries):
            try:
                self._random_delay(1, 2)
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                if attempt == retries - 1:
                    print(f"Ошибка получения страницы {url}: {e}")
                    return None
                time.sleep(2 ** attempt)  # Экспоненциальная задержка
        return None
    
    @abstractmethod
    def parse_reviews(self, url: str) -> List[Dict]:
        """
        Парсинг отзывов с маркетплейса
        
        Args:
            url: URL товара
            
        Returns:
            Список словарей с отзывами:
            [{
                'author': str,
                'rating': int,
                'text': str,
                'date': datetime
            }, ...]
        """
        pass
    
    @abstractmethod
    def get_product_name(self, url: str) -> Optional[str]:
        """Получение названия товара"""
        pass

