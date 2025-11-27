"""
Парсеры для различных маркетплейсов
"""
from .wildberries_parser import WildberriesParser
from .ozon_parser import OzonParser
from .yandex_market_parser import YandexMarketParser
from .base_parser import BaseParser

__all__ = ['WildberriesParser', 'OzonParser', 'YandexMarketParser', 'BaseParser']

