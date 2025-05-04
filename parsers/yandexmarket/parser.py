from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from parsers.common.base_parser import BaseParser
import logging
import json
import re
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

class YandexMarketParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.base_url = "https://market.yandex.ru"
        self.marketplace_name = "yandexmarket"
        self.search_url = f"{self.base_url}/search"
        self.api_base_url = "https://market.yandex.ru/api/v2"
    
    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Поиск товаров на Яндекс.Маркет"""
        try:
            # Формируем URL для поиска
            encoded_query = quote(query)
            search_url = f"{self.search_url}?text={encoded_query}"
            
            result = await self.browser_manager.search_products(search_url, self.marketplace_name, query)
            
            if result["status"] == "error":
                logger.error(f"Error searching products: {result['error']}")
                return []
            
            products = await self.parse_search_page(result["html"])
            
            # Получаем детальную информацию о каждом товаре
            detailed_products = []
            for product in products[:10]:  # Ограничиваем количество товаров для детального парсинга
                try:
                    details = await self.get_product_details(product["url"])
                    detailed_products.append({**product, **details})
                except Exception as e:
                    logger.error(f"Error getting details for product {product['url']}: {e}")
                    detailed_products.append(product)
            
            await self.save_results(detailed_products, query)
            return detailed_products
            
        except Exception as e:
            logger.error(f"Error in search_products: {e}")
            return []
    
    async def parse_search_page(self, html: str) -> List[Dict[str, Any]]:
        """Парсинг страницы с результатами поиска"""
        products = []
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Находим все карточки товаров
            product_cards = soup.select('div[data-zone-name="snippet"]')
            
            for card in product_cards:
                try:
                    # Извлекаем основную информацию о товаре
                    title_elem = card.select_one('h3[data-zone-name="title"]')
                    price_elem = card.select_one('span[data-zone-name="price"]')
                    url_elem = card.select_one('a[href*="/product/"]')
                    shop_elem = card.select_one('span[data-zone-name="shop-name"]')
                    rating_elem = card.select_one('span[data-zone-name="rating"]')
                    # Добавляем парсинг фото
                    photo_elem = card.select_one('img[data-zone-name="image"]')
                    photo = photo_elem['src'] if photo_elem and photo_elem.has_attr('src') else ''
                    if not all([title_elem, url_elem]):
                        continue
                    
                    # Получаем ID товара из URL
                    product_id = re.search(r'/product/(\d+)/', url_elem['href'])
                    if not product_id:
                        continue
                    
                    title = self._clean_text(title_elem.text)
                    url = urljoin(self.base_url, url_elem['href'])
                    price = await self._extract_price(price_elem.text) if price_elem else 0.0
                    shop = self._clean_text(shop_elem.text) if shop_elem else ""
                    rating = float(rating_elem.text.replace(',', '.')) if rating_elem else 0.0
                    
                    product = {
                        "title": title,
                        "url": url,
                        "price": price,
                        "seller": shop,
                        "rating": rating,
                        "marketplace": self.marketplace_name,
                        "product_id": product_id.group(1),
                        "photo": photo
                    }
                    
                    products.append(product)
                except Exception as e:
                    logger.error(f"Error parsing product card: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing search page: {e}")
        
        return products
    
    async def get_reviews(self, product_url: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение отзывов о товаре"""
        try:
            reviews = []
            product_id = re.search(r'/product/(\d+)/', product_url)
            if not product_id:
                logger.error(f"Could not extract product ID from URL: {product_url}")
                return reviews
            
            # URL для API отзывов
            reviews_url = f"{self.api_base_url}/product/{product_id.group(1)}/reviews"
            
            # Получаем отзывы через API
            result = await self.browser_manager.search_products(reviews_url, self.marketplace_name, "")
            
            if result["status"] == "error":
                return reviews
            
            try:
                data = json.loads(result["html"])
                reviews_data = data.get("reviews", [])
                
                for review in reviews_data[:limit]:
                    try:
                        review_item = {
                            "text": self._clean_text(review.get("text", "")),
                            "rating": float(review.get("rating", 0)),
                            "author": review.get("author", {}).get("name", "Аноним"),
                            "date": review.get("date", ""),
                            "likes": review.get("votes", {}).get("helpful", 0),
                            "dislikes": review.get("votes", {}).get("unhelpful", 0),
                            "verified_purchase": review.get("verified", False)
                        }
                        
                        # Добавляем фотографии, если есть
                        photos = review.get("photos", [])
                        if photos:
                            review_item["photos"] = [
                                photo.get("url")
                                for photo in photos
                                if photo.get("url")
                            ]
                        
                        # Добавляем достоинства и недостатки
                        pros = review.get("pros", "").strip()
                        cons = review.get("cons", "").strip()
                        if pros:
                            review_item["pros"] = pros
                        if cons:
                            review_item["cons"] = cons
                        
                        reviews.append(review_item)
                    except Exception as e:
                        logger.error(f"Error processing review: {e}")
                        continue
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing reviews JSON: {e}")
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error getting reviews: {e}")
            return []
    
    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """Получение детальной информации о товаре"""
        try:
            result = await self.browser_manager.search_products(product_url, self.marketplace_name, "")
            
            if result["status"] == "error":
                return {}
            
            soup = BeautifulSoup(result["html"], 'lxml')
            
            # Извлекаем детальную информацию
            details = {
                "description": "",
                "characteristics": {},
                "seller": "",
                "rating": 0.0,
                "reviews_count": 0,
                "reviews": [],
                "photo": ""
            }
            
            # Описание товара
            description_elem = soup.select_one('div[data-zone-name="description"]')
            if description_elem:
                details["description"] = self._clean_text(description_elem.text)
            
            # Характеристики
            chars_container = soup.select('div[data-zone-name="specifications"] dl')
            for char in chars_container:
                try:
                    key = self._clean_text(char.select_one('dt').text)
                    value = self._clean_text(char.select_one('dd').text)
                    details["characteristics"][key] = value
                except:
                    continue
            
            # Продавец
            seller_elem = soup.select_one('span[data-zone-name="shop-name"]')
            if seller_elem:
                details["seller"] = self._clean_text(seller_elem.text)
            
            # Рейтинг и количество отзывов
            rating_elem = soup.select_one('span[data-zone-name="rating"]')
            if rating_elem:
                try:
                    details["rating"] = float(rating_elem.text.replace(',', '.'))
                except:
                    pass
            
            reviews_count_elem = soup.select_one('span[data-zone-name="total-reviews"]')
            if reviews_count_elem:
                try:
                    count_text = reviews_count_elem.text
                    count = int(re.search(r'\d+', count_text).group())
                    details["reviews_count"] = count
                except:
                    pass
            
            # Фото товара (детальная страница)
            photo_elem = soup.select_one('img[data-zone-name="image"]')
            if photo_elem and photo_elem.has_attr('src'):
                details["photo"] = photo_elem['src']
            
            # Получаем отзывы
            reviews = await self.get_reviews(product_url)
            details["reviews"] = reviews
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return {} 