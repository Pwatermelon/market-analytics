import logging
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductParser:
    """Базовый класс для парсинга товаров"""
    
    def __init__(self, marketplace: str):
        self.marketplace = marketplace
    
    def parse_products(self, html: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Парсинг товаров из HTML"""
        if not html:
            logger.error(f"Empty HTML for {self.marketplace}")
            return []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            products = self._extract_products(soup, limit)
            logger.info(f"Successfully parsed {len(products)} products from {self.marketplace}")
            return products
        except Exception as e:
            logger.error(f"Error parsing products from {self.marketplace}: {str(e)}", exc_info=True)
            return []
    
    def _extract_products(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        """Извлечение товаров из HTML (должен быть переопределен в подклассах)"""
        raise NotImplementedError("Subclasses must implement _extract_products method")
    
    def _clean_price(self, price_text: str) -> float:
        """Очистка цены от нечисловых символов"""
        if not price_text:
            return 0.0
        
        # Удаляем все символы кроме цифр и точки
        cleaned = re.sub(r'[^\d.]', '', price_text)
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def _clean_rating(self, rating_text: str) -> Optional[float]:
        """Очистка рейтинга от нечисловых символов"""
        if not rating_text:
            return None
        
        # Удаляем все символы кроме цифр и точки
        cleaned = re.sub(r'[^\d.]', '', rating_text)
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None


class WildberriesParser(ProductParser):
    """Парсер для Wildberries"""
    
    def __init__(self):
        super().__init__("wildberries")
    
    def _extract_products(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        products = []
        
        # Ищем карточки товаров
        product_cards = soup.select('.product-card')
        if not product_cards:
            product_cards = soup.select('.catalog-item')
        if not product_cards:
            product_cards = soup.select('.product-card__main')
        
        logger.info(f"Found {len(product_cards)} product cards on Wildberries")
        
        for card in product_cards[:limit]:
            try:
                # Извлекаем ID товара
                product_id = card.get('data-product-id', '')
                if not product_id:
                    # Пробуем найти ID в ссылке
                    link = card.select_one('a[href*="/catalog/"]')
                    if link and 'href' in link.attrs:
                        href = link['href']
                        match = re.search(r'/catalog/(\d+)/', href)
                        if match:
                            product_id = match.group(1)
                
                # Извлекаем название
                name_elem = card.select_one('.product-card__name')
                if not name_elem:
                    name_elem = card.select_one('.catalog-item__name')
                name = name_elem.text.strip() if name_elem else ''
                
                # Извлекаем цену
                price_elem = card.select_one('.product-card__price')
                if not price_elem:
                    price_elem = card.select_one('.catalog-item__price')
                price_text = price_elem.text.strip() if price_elem else '0'
                price = self._clean_price(price_text)
                
                # Извлекаем описание
                desc_elem = card.select_one('.product-card__description')
                description = desc_elem.text.strip() if desc_elem else ''
                
                # Извлекаем рейтинг
                rating_elem = card.select_one('.product-card__rating')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating = self._clean_rating(rating_text)
                
                # Создаем объект товара
                product = {
                    "id": product_id,
                    "name": name,
                    "price": price,
                    "url": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
                    "description": description,
                    "rating": rating,
                    "marketplace": "wildberries"
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Wildberries product card: {str(e)}", exc_info=True)
                continue
        
        return products


class OzonParser(ProductParser):
    """Парсер для Ozon"""
    
    def __init__(self):
        super().__init__("ozon")
    
    def _extract_products(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        products = []
        
        # Ищем карточки товаров
        product_cards = soup.select('.tile-hover-target')
        if not product_cards:
            product_cards = soup.select('.product-card')
        if not product_cards:
            product_cards = soup.select('.tsBody500')
        
        logger.info(f"Found {len(product_cards)} product cards on Ozon")
        
        for card in product_cards[:limit]:
            try:
                # Извлекаем ID товара
                product_id = card.get('data-product-id', '')
                if not product_id:
                    # Пробуем найти ID в ссылке
                    link = card.select_one('a[href*="/product/"]')
                    if link and 'href' in link.attrs:
                        href = link['href']
                        match = re.search(r'/product/(\d+)/', href)
                        if match:
                            product_id = match.group(1)
                
                # Извлекаем название
                name_elem = card.select_one('.tsBody500')
                if not name_elem:
                    name_elem = card.select_one('.product-card__name')
                if not name_elem:
                    name_elem = card.select_one('.product-card__title')
                name = name_elem.text.strip() if name_elem else ''
                
                # Извлекаем цену
                price_elem = card.select_one('.c2h5')
                if not price_elem:
                    price_elem = card.select_one('.product-card__price')
                if not price_elem:
                    price_elem = card.select_one('.price')
                price_text = price_elem.text.strip() if price_elem else '0'
                price = self._clean_price(price_text)
                
                # Извлекаем описание
                desc_elem = card.select_one('.product-card__description')
                description = desc_elem.text.strip() if desc_elem else ''
                
                # Извлекаем рейтинг
                rating_elem = card.select_one('.rating')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating = self._clean_rating(rating_text)
                
                # Создаем объект товара
                product = {
                    "id": product_id,
                    "name": name,
                    "price": price,
                    "url": f"https://www.ozon.ru/product/{product_id}/",
                    "description": description,
                    "rating": rating,
                    "marketplace": "ozon"
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Ozon product card: {str(e)}", exc_info=True)
                continue
        
        return products


class GoldAppleParser(ProductParser):
    """Парсер для Gold Apple"""
    
    def __init__(self):
        super().__init__("goldapple")
    
    def _extract_products(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        products = []
        
        # Ищем карточки товаров
        product_cards = soup.select('.product-card')
        if not product_cards:
            product_cards = soup.select('.catalog-item')
        if not product_cards:
            product_cards = soup.select('.product-item')
        
        logger.info(f"Found {len(product_cards)} product cards on Gold Apple")
        
        for card in product_cards[:limit]:
            try:
                # Извлекаем ID товара
                product_id = card.get('data-product-id', '')
                if not product_id:
                    # Пробуем найти ID в ссылке
                    link = card.select_one('a[href*="/product/"]')
                    if link and 'href' in link.attrs:
                        href = link['href']
                        match = re.search(r'/product/(\d+)/', href)
                        if match:
                            product_id = match.group(1)
                
                # Извлекаем название
                name_elem = card.select_one('.product-card__name')
                if not name_elem:
                    name_elem = card.select_one('.catalog-item__name')
                if not name_elem:
                    name_elem = card.select_one('.product-item__name')
                name = name_elem.text.strip() if name_elem else ''
                
                # Извлекаем цену
                price_elem = card.select_one('.product-card__price')
                if not price_elem:
                    price_elem = card.select_one('.catalog-item__price')
                if not price_elem:
                    price_elem = card.select_one('.product-item__price')
                price_text = price_elem.text.strip() if price_elem else '0'
                price = self._clean_price(price_text)
                
                # Извлекаем описание
                desc_elem = card.select_one('.product-card__description')
                if not desc_elem:
                    desc_elem = card.select_one('.catalog-item__description')
                description = desc_elem.text.strip() if desc_elem else ''
                
                # Извлекаем рейтинг
                rating_elem = card.select_one('.product-card__rating')
                if not rating_elem:
                    rating_elem = card.select_one('.catalog-item__rating')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating = self._clean_rating(rating_text)
                
                # Создаем объект товара
                product = {
                    "id": product_id,
                    "name": name,
                    "price": price,
                    "url": f"https://goldapple.ru/product/{product_id}/",
                    "description": description,
                    "rating": rating,
                    "marketplace": "goldapple"
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Gold Apple product card: {str(e)}", exc_info=True)
                continue
        
        return products 