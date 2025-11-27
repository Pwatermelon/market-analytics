"""
Простой и надежный парсер для Wildberries через API
"""
from typing import List, Dict, Optional
from datetime import datetime
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from .base_parser import BaseParser


class WildberriesParserSimple(BaseParser):
    """Простой парсер Wildberries через API"""
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Referer': 'https://www.wildberries.ru/',
        })
        self.driver = None
    
    def _extract_article(self, url: str) -> Optional[str]:
        """Извлечение артикула"""
        match = re.search(r'/catalog/(\d+)(?:/|$)', url)
        return match.group(1) if match else None
    
    def _init_driver(self):
        """Инициализация браузера"""
        if self.driver:
            return
        try:
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            self.driver = uc.Chrome(options=options, version_main=None)
        except:
            self.driver = None
    
    def get_product_name(self, url: str) -> Optional[str]:
        """Получение названия товара"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                h1 = soup.find('h1')
                if h1:
                    return h1.get_text(strip=True)
        except:
            pass
        return None
    
    def parse_reviews(self, url: str) -> List[Dict]:
        """Парсинг отзывов через API"""
        article = self._extract_article(url)
        if not article:
            print("❌ Не удалось извлечь артикул")
            return []
        
        reviews = []
        
        # Метод 1: Пробуем API отзывов
        try:
            api_url = f"https://feedbacks1.wildberries.ru/api/v1/summary/full"
            params = {'nmId': article}
            response = self.session.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'feedbacks' in data:
                    for fb in data['feedbacks']:
                        text = fb.get('text', '').strip()
                        if not text or len(text) < 10:
                            continue
                        
                        date_str = fb.get('createdDate', '')
                        date = datetime.now()
                        if date_str:
                            try:
                                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            except:
                                pass
                        
                        reviews.append({
                            "author": fb.get('wbUserDetails', {}).get('name', 'Аноним'),
                            "rating": fb.get('productValuation', 0),
                            "text": text,
                            "date": date
                        })
                    
                    if reviews:
                        print(f"✅ API вернул {len(reviews)} отзывов")
                        return reviews
        except Exception as e:
            print(f"⚠️ API не сработал: {e}")
        
        # Метод 2: Selenium парсинг
        print("🔄 Переключаюсь на Selenium...")
        self._init_driver()
        if not self.driver:
            return []
        
        try:
            feedback_url = f"https://www.wildberries.ru/catalog/{article}/feedbacks"
            self.driver.get(feedback_url)
            time.sleep(5)
            
            # Прокручиваем
            for i in range(10):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Извлекаем через JS
            js_code = """
            const reviews = [];
            const items = document.querySelectorAll('[data-feedback-id], .feedback-item, article');
            items.forEach(item => {
                const text = item.innerText || '';
                if (text.length < 30) return;
                const author = item.querySelector('strong, b, [class*="author"]')?.innerText || 'Аноним';
                const rating = item.querySelectorAll('[class*="star"][class*="fill"], [class*="star"].active').length || 0;
                reviews.push({author, rating, text: text.trim()});
            });
            return reviews;
            """
            
            result = self.driver.execute_script(js_code)
            for item in result:
                reviews.append({
                    "author": item.get('author', 'Аноним'),
                    "rating": item.get('rating', 0),
                    "text": item.get('text', ''),
                    "date": datetime.now()
                })
        except Exception as e:
            print(f"❌ Ошибка Selenium: {e}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
        
        return reviews
    
    def __del__(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

