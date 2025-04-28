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
        
        try:
            # Удаляем все символы кроме цифр, точки и запятой
            cleaned = re.sub(r'[^\d.,]', '', price_text)
            
            # Заменяем запятую на точку
            cleaned = cleaned.replace(',', '.')
            
            # Если есть несколько точек, оставляем только первую
            if cleaned.count('.') > 1:
                cleaned = cleaned.replace('.', '', cleaned.count('.') - 1)
            
            # Преобразуем в float
            price = float(cleaned)
            
            # Если цена слишком большая (вероятно, ошибка парсинга), делим на 100
            if price > 1000000:
                price = price / 100
            
            return price
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
        
        # Ищем карточки товаров с разными селекторами
        product_cards = []
        selectors = [
            '.product-card',
            '.catalog-item',
            '.product-card__main',
            '[data-product-id]',  # Ищем по атрибуту data-product-id
            '.product-card__container',  # Новый селектор
            '.catalog-item__container'   # Новый селектор
        ]
        
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                product_cards = cards
                logger.info(f"Found {len(cards)} product cards using selector: {selector}")
                break
        
        if not product_cards:
            logger.warning("No product cards found with any selector")
            # Попробуем найти товары по другим признакам
            product_cards = soup.find_all('div', class_=lambda x: x and ('product' in x.lower() or 'card' in x.lower()))
            logger.info(f"Found {len(product_cards)} product cards using alternative search")
        
        logger.info(f"Total found {len(product_cards)} product cards on Wildberries")
        
        for card in product_cards[:limit]:
            try:
                # Извлекаем ID товара
                product_id = card.get('data-product-id', '')
                if not product_id:
                    # Пробуем найти ID в ссылке
                    links = card.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        # Ищем ID в разных форматах URL
                        patterns = [
                            r'/catalog/(\d+)/',
                            r'/product/(\d+)/',
                            r'/(\d+)/detail',
                            r'id=(\d+)'
                        ]
                        for pattern in patterns:
                            match = re.search(pattern, href)
                            if match:
                                product_id = match.group(1)
                                break
                        if product_id:
                            break
                
                if not product_id:
                    logger.warning("Could not find product ID, skipping product")
                    continue
                
                # Извлекаем название
                name = ''
                name_selectors = [
                    '.product-card__name',
                    '.catalog-item__name',
                    '.product-card__title',
                    '.catalog-item__title',
                    'h3',  # Часто название в h3
                    '[class*="name"]',  # Ищем по частичному совпадению класса
                    '[class*="title"]'  # Ищем по частичному совпадению класса
                ]
                
                for selector in name_selectors:
                    name_elem = card.select_one(selector)
                    if name_elem and name_elem.text.strip():
                        name = name_elem.text.strip()
                        break
                
                if not name:
                    logger.warning(f"Could not find product name for ID {product_id}, skipping product")
                    continue
                
                # --- Цена ---
                price = 0.0
                price_elem = card.select_one('.price__lower-price, .price__current, .price__wrapper, [class*="price"]')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self._clean_price(price_text)
                else:
                    # Попробовать найти рубли и копейки по отдельности
                    rub_elem = card.select_one('.price__rub')
                    kop_elem = card.select_one('.price__kop')
                    if rub_elem:
                        rub = rub_elem.get_text(strip=True)
                        kop = kop_elem.get_text(strip=True) if kop_elem else '00'
                        try:
                            price = float(f'{rub}.{kop}')
                        except Exception:
                            price = 0.0
                
                # --- Картинка ---
                image_url = ''
                img_elem = card.select_one('img')
                if img_elem:
                    image_url = img_elem.get('data-src') or img_elem.get('src') or img_elem.get('data-original') or ''
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    elif image_url.startswith('/'):
                        image_url = 'https://www.wildberries.ru' + image_url
                
                # --- Описание ---
                description = ''
                desc_selectors = [
                    '.product-card__description',
                    '.catalog-item__description',
                    '[class*="description"]',
                    '[class*="desc"]'
                ]
                for selector in desc_selectors:
                    desc_elem = card.select_one(selector)
                    if desc_elem:
                        description = desc_elem.text.strip()
                        break
                
                # --- Рейтинг ---
                rating = None
                # Ищем средний рейтинг (звезды), а не количество отзывов
                rating_elem = card.select_one('[class*="rating"] [class*="star"]')
                if rating_elem and rating_elem.get('aria-label'):
                    # Например: aria-label="4.9 из 5"
                    m = re.search(r'([\d.,]+)', rating_elem['aria-label'])
                    if m:
                        try:
                            rating = float(m.group(1).replace(',', '.'))
                        except Exception:
                            rating = None
                else:
                    # Фоллбек: ищем просто число с плавающей точкой
                    rating_text = None
                    rating_block = card.select_one('.product-card__rating, [class*="rating"]')
                    if rating_block:
                        rating_text = rating_block.get_text(strip=True).replace(',', '.')
                        try:
                            val = float(rating_text)
                            # Если рейтинг явно в диапазоне 0-5, используем
                            if 0 < val <= 5:
                                rating = val
                        except Exception:
                            rating = None
                
                # Создаем объект товара
                product = {
                    "id": product_id,
                    "name": name,
                    "price": price,
                    "url": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
                    "description": description,
                    "rating": rating,
                    "marketplace": "wildberries",
                    "image_url": image_url
                }
                
                products.append(product)
                logger.info(f"Successfully parsed product: {name} (ID: {product_id})")
                
            except Exception as e:
                logger.error(f"Error parsing Wildberries product card: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Successfully parsed {len(products)} products from Wildberries")
        return products


class YandexMarketParser(ProductParser):
    """Парсер для Яндекс Маркета"""
    
    def __init__(self):
        super().__init__("yandexmarket")
    
    def _extract_products(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        products = []
        
        # Ищем карточки товаров
        product_cards = soup.select('div[data-zone-name="snippet"]')
        
        if not product_cards:
            logger.warning("No product cards found on Yandex Market")
            return []
        
        logger.info(f"Found {len(product_cards)} product cards on Yandex Market")
        
        for card in product_cards[:limit]:
            try:
                # Извлекаем ID товара
                product_id = card.get('data-id', '')
                if not product_id:
                    # Пробуем найти ID в ссылке
                    link = card.select_one('a[href*="/product/"]')
                    if link and link.get('href'):
                        product_id = link['href'].split('/')[-1]
                
                if not product_id:
                    logger.warning("Could not find product ID, skipping product")
                    continue
                
                # Извлекаем название
                name = ''
                name_elem = card.select_one('h3[class*="title"]')
                if name_elem:
                    name = name_elem.text.strip()
                
                if not name:
                    logger.warning(f"Could not find product name for ID {product_id}, skipping product")
                    continue
                
                # Извлекаем цену
                price = 0.0
                price_elem = card.select_one('span[data-auto="value"]')
                if price_elem:
                    price_text = price_elem.text.strip()
                    price = self._clean_price(price_text)
                
                # Извлекаем картинку
                image_url = ''
                img_elem = card.select_one('img')
                if img_elem:
                    image_url = img_elem.get('src', '')
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                
                # Извлекаем рейтинг
                rating = None
                rating_elem = card.select_one('span[data-auto="rating"]')
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating = self._clean_rating(rating_text)
                
                # Извлекаем описание
                description = ''
                desc_elem = card.select_one('div[class*="description"]')
                if desc_elem:
                    description = desc_elem.text.strip()
                
                # Создаем объект товара
                product = {
                    "id": product_id,
                    "name": name,
                    "price": price,
                    "url": f"https://market.yandex.ru/product/{product_id}",
                    "description": description,
                    "rating": rating,
                    "marketplace": "yandexmarket",
                    "image_url": image_url
                }
                
                products.append(product)
                logger.info(f"Successfully parsed product: {name} (ID: {product_id})")
                
            except Exception as e:
                logger.error(f"Error parsing Yandex Market product card: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Successfully parsed {len(products)} products from Yandex Market")
        return products


class OzonParser(ProductParser):
    """Парсер для Ozon"""
    
    def __init__(self):
        super().__init__("ozon")
    
    def _extract_products(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        products = []
        
        # Ищем карточки товаров
        product_cards = soup.select('div[data-widget="searchResultsV2"] div[data-index]')
        
        if not product_cards:
            logger.warning("No product cards found on Ozon")
            return []
        
        logger.info(f"Found {len(product_cards)} product cards on Ozon")
        
        for card in product_cards[:limit]:
            try:
                # Извлекаем ID товара
                product_id = card.get('data-id', '')
                if not product_id:
                    # Пробуем найти ID в ссылке
                    link = card.select_one('a[href*="/product/"]')
                    if link and link.get('href'):
                        product_id = link['href'].split('/')[-1]
                
                if not product_id:
                    logger.warning("Could not find product ID, skipping product")
                    continue
                
                # Извлекаем название
                name = ''
                name_elem = card.select_one('span[class*="title"]')
                if name_elem:
                    name = name_elem.text.strip()
                
                if not name:
                    logger.warning(f"Could not find product name for ID {product_id}, skipping product")
                    continue
                
                # Извлекаем цену
                price = 0.0
                price_elem = card.select_one('span[class*="price"]')
                if price_elem:
                    price_text = price_elem.text.strip()
                    price = self._clean_price(price_text)
                
                # Извлекаем картинку
                image_url = ''
                img_elem = card.select_one('img')
                if img_elem:
                    image_url = img_elem.get('src', '')
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                
                # Извлекаем рейтинг
                rating = None
                rating_elem = card.select_one('span[class*="rating"]')
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating = self._clean_rating(rating_text)
                
                # Извлекаем описание
                description = ''
                desc_elem = card.select_one('div[class*="description"]')
                if desc_elem:
                    description = desc_elem.text.strip()
                
                # Создаем объект товара
                product = {
                    "id": product_id,
                    "name": name,
                    "price": price,
                    "url": f"https://www.ozon.ru/product/{product_id}",
                    "description": description,
                    "rating": rating,
                    "marketplace": "ozon",
                    "image_url": image_url
                }
                
                products.append(product)
                logger.info(f"Successfully parsed product: {name} (ID: {product_id})")
                
            except Exception as e:
                logger.error(f"Error parsing Ozon product card: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Successfully parsed {len(products)} products from Ozon")
        return products


class GoldAppleParser(ProductParser):
    """Парсер для Gold Apple"""
    
    def __init__(self):
        super().__init__("goldapple")
    
    def _extract_products(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, Any]]:
        products = []
        
        # Ищем карточки товаров
        product_cards = soup.select('div[class*="product-card"]')
        
        if not product_cards:
            logger.warning("No product cards found on Gold Apple")
            return []
        
        logger.info(f"Found {len(product_cards)} product cards on Gold Apple")
        
        for card in product_cards[:limit]:
            try:
                # Извлекаем ID товара
                product_id = card.get('data-product-id', '')
                if not product_id:
                    # Пробуем найти ID в ссылке
                    link = card.select_one('a[href*="/product/"]')
                    if link and link.get('href'):
                        product_id = link['href'].split('/')[-1]
                
                if not product_id:
                    logger.warning("Could not find product ID, skipping product")
                    continue
                
                # Извлекаем название
                name = ''
                name_elem = card.select_one('div[class*="product-name"]')
                if name_elem:
                    name = name_elem.text.strip()
                
                if not name:
                    logger.warning(f"Could not find product name for ID {product_id}, skipping product")
                    continue
                
                # Извлекаем цену
                price = 0.0
                price_elem = card.select_one('div[class*="price"]')
                if price_elem:
                    price_text = price_elem.text.strip()
                    price = self._clean_price(price_text)
                
                # Извлекаем картинку
                image_url = ''
                img_elem = card.select_one('img')
                if img_elem:
                    image_url = img_elem.get('src', '')
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                
                # Извлекаем рейтинг
                rating = None
                rating_elem = card.select_one('div[class*="rating"]')
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating = self._clean_rating(rating_text)
                
                # Извлекаем описание
                description = ''
                desc_elem = card.select_one('div[class*="description"]')
                if desc_elem:
                    description = desc_elem.text.strip()
                
                # Создаем объект товара
                product = {
                    "id": product_id,
                    "name": name,
                    "price": price,
                    "url": f"https://goldapple.ru/product/{product_id}",
                    "description": description,
                    "rating": rating,
                    "marketplace": "goldapple",
                    "image_url": image_url
                }
                
                products.append(product)
                logger.info(f"Successfully parsed product: {name} (ID: {product_id})")
                
            except Exception as e:
                logger.error(f"Error parsing Gold Apple product card: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Successfully parsed {len(products)} products from Gold Apple")
        return products 