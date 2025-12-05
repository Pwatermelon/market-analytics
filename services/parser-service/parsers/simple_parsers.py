"""
Простые и надежные парсеры для всех маркетплейсов
Использует Playwright для надежной работы в Docker
Все вызовы Playwright обернуты в ThreadPoolExecutor для работы с asyncio
"""
from typing import List, Dict, Optional
from datetime import datetime
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page
import concurrent.futures
from .base_parser import BaseParser


def _run_playwright_in_thread(func):
    """Обертка для запуска sync_playwright в отдельном потоке"""
    def wrapper(*args, **kwargs):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(func, *args, **kwargs)
            return future.result(timeout=300)  # 5 минут таймаут
    return wrapper


class SimpleWildberriesParser(BaseParser):
    """Простой парсер Wildberries"""
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
    
    def _extract_article(self, url: str) -> Optional[str]:
        match = re.search(r'/catalog/(\d+)(?:/|$)', url)
        return match.group(1) if match else None
    
    def get_product_name(self, url: str) -> Optional[str]:
        try:
            r = self.session.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            h1 = soup.find('h1')
            return h1.get_text(strip=True) if h1 else None
        except:
            return None
    
    def parse_reviews(self, url: str) -> List[Dict]:
        article = self._extract_article(url)
        if not article:
            print(f"❌ Не удалось извлечь артикул из URL: {url}")
            return []
        
        print(f"🔍 Извлечен артикул: {article}")
        
        # API метод
        try:
            print(f"🌐 Пробую API метод для артикула {article}...")
            api_url = f"https://feedbacks1.wildberries.ru/api/v1/summary/full"
            headers = {
                'Referer': f'https://www.wildberries.ru/catalog/{article}/detail.aspx',
                'Accept': 'application/json',
            }
            r = self.session.get(api_url, params={'nmId': article}, headers=headers, timeout=15)
            print(f"📡 API ответ: статус {r.status_code}")
            
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"📊 API вернул данные, ключи: {list(data.keys())}")
                    feedbacks = data.get('feedbacks', [])
                    print(f"📝 Найдено отзывов в API: {len(feedbacks)}")
                    
                    reviews = []
                    for fb in feedbacks:
                        text = fb.get('text', '').strip()
                        if text and len(text) > 10:
                            date_str = fb.get('createdDate', '')
                            date = datetime.now()
                            try:
                                if date_str:
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
                    else:
                        print(f"⚠️ API вернул 0 отзывов, пробую Playwright...")
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка парсинга JSON: {e}")
                    print(f"Ответ API: {r.text[:500]}")
            else:
                print(f"❌ API вернул статус {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"❌ Ошибка API метода: {e}")
            import traceback
            print(traceback.format_exc())
        
        # Fallback на Playwright (надежнее чем Selenium)
        print("🔄 Переключаюсь на Playwright парсинг...")
        try:
            def _playwright_parse():
                with sync_playwright() as p:
                    print("🚀 Запускаю браузер Playwright...")
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                    )
                    page = browser.new_page()
                    page.set_viewport_size({"width": 1920, "height": 1080})
                    
                    feedback_url = f"https://www.wildberries.ru/catalog/{article}/feedbacks"
                    print(f"🌐 Открываю страницу отзывов: {feedback_url}")
                    page.goto(feedback_url, wait_until="networkidle", timeout=30000)
                    time.sleep(3)
                    
                    # Прокручиваем для загрузки
                    print("📜 Прокручиваю страницу...")
                    for i in range(15):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(2)
                        
                        # Ищем кнопки "Показать еще"
                        try:
                            buttons = page.query_selector_all("button")
                            for btn in buttons:
                                try:
                                    text = btn.inner_text().lower()
                                    if any(word in text for word in ["показать", "еще", "загрузить"]):
                                        btn.click()
                                        print(f"✅ Кликнул кнопку")
                                        time.sleep(3)
                                except:
                                    continue
                        except:
                            pass
                    
                    # Извлекаем через JS
                    print("🔍 Извлекаю отзывы через JavaScript...")
                    js_code = """
                    const reviews = [];
                    const selectors = [
                        '[data-feedback-id]',
                        '.feedback-item',
                        'article',
                        '[class*="feedback"]'
                    ];
                    
                    let items = [];
                    for (let sel of selectors) {
                        items.push(...document.querySelectorAll(sel));
                    }
                    
                    items = Array.from(new Set(items));
                    console.log('Найдено элементов:', items.length);
                    
                    items.forEach(item => {
                        const text = (item.innerText || item.textContent || '').trim();
                        if (text.length < 30) return;
                        
                        // Пропускаем служебные элементы
                        if (text.toLowerCase().includes('cookie') || 
                            text.toLowerCase().includes('политика')) return;
                        
                        const author = item.querySelector('strong, b, [class*="author"]')?.innerText?.trim() || 'Аноним';
                        const stars = item.querySelectorAll('[class*="star"][class*="fill"], [class*="star"].active, .star-fill').length || 0;
                        
                        if (text.length > 20) {
                            reviews.push({
                                author: author.length > 50 ? 'Аноним' : author,
                                rating: stars,
                                text: text
                            });
                        }
                    });
                    
                    return reviews;
                    """
                    
                    result = page.evaluate(js_code)
                    print(f"📊 JavaScript нашел {len(result) if result else 0} элементов")
                    
                    reviews = []
                    seen_texts = set()
                    for item in (result or []):
                        text = item.get('text', '').strip()
                        if not text or len(text) < 20:
                            continue
                        
                        # Проверка дубликатов
                        text_hash = hash(text[:100])
                        if text_hash in seen_texts:
                            continue
                        seen_texts.add(text_hash)
                        
                        reviews.append({
                            "author": item.get('author', 'Аноним'),
                            "rating": item.get('rating', 0),
                            "text": text,
                            "date": datetime.now()
                        })
                    
                    browser.close()
                    return reviews
            
            # Запускаем в отдельном потоке
            print("📝 Запускаю ThreadPoolExecutor для Wildberries...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                print("📝 Отправляю задачу в поток...")
                future = executor.submit(_playwright_parse)
                print("📝 Ожидаю результат (таймаут 300 сек)...")
                reviews = future.result(timeout=300)  # 5 минут таймаут
                print(f"📝 Получен результат: {len(reviews) if reviews else 0} отзывов")
                
                if reviews:
                    print(f"✅ Playwright нашел {len(reviews)} отзывов")
                    return reviews
                else:
                    print(f"❌ Playwright не нашел отзывов")
                    
        except Exception as e:
            print(f"❌ Ошибка Playwright: {e}")
            import traceback
            print(traceback.format_exc())
        
        return []


class SimpleOzonParser(BaseParser):
    """Простой парсер Ozon с Playwright"""
    
    def __init__(self):
        super().__init__()
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        match = re.search(r'/product/(\d+)(?:/|\?|$)', url)
        if match:
            return match.group(1)
        match = re.search(r'/product/[^/]+-(\d+)(?:/|\?|$)', url)
        return match.group(1) if match else None
    
    def get_product_name(self, url: str) -> Optional[str]:
        try:
            def _get_name():
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                    )
                    page = browser.new_page()
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    time.sleep(2)
                    h1 = page.query_selector('h1')
                    name = h1.inner_text().strip() if h1 else None
                    browser.close()
                    return name
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_get_name)
                return future.result(timeout=60)
        except:
            return None
    
    def parse_reviews(self, url: str) -> List[Dict]:
        product_id = self._extract_product_id(url)
        if not product_id:
            print(f"❌ Не удалось извлечь ID товара из URL: {url}")
            return []
        
        print(f"🔍 Извлечен ID товара: {product_id}")
        print("🚀 Запускаю Playwright для Ozon...")
        print("📝 [MAIN] Перед запуском ThreadPoolExecutor...")
        
        reviews = []
        try:
            def _playwright_parse():
                print("📝 [THREAD] Начало выполнения в отдельном потоке для Ozon...")
                import sys
                sys.stdout.flush()
                try:
                    print("📝 [THREAD] Инициализация Playwright...")
                    sys.stdout.flush()
                    with sync_playwright() as p:
                        print("📝 [THREAD] Playwright инициализирован, запускаю браузер...")
                        browser = p.chromium.launch(
                            headless=True,
                            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                        )
                        print("📝 [THREAD] Браузер запущен, создаю страницу...")
                        page = browser.new_page()
                        page.set_viewport_size({"width": 1920, "height": 1080})
                        
                        review_url = f"https://www.ozon.ru/product/{product_id}/reviews/"
                        print(f"🌐 Открываю страницу отзывов: {review_url}")
                        page.goto(review_url, wait_until="networkidle", timeout=30000)
                        time.sleep(3)
                        
                        print("📜 Прокручиваю страницу...")
                        for i in range(15):
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(2)
                            
                            # Ищем кнопки "Показать еще"
                            try:
                                buttons = page.query_selector_all("button")
                                for btn in buttons:
                                    try:
                                        text = btn.inner_text().lower()
                                        if any(word in text for word in ["показать", "еще", "загрузить"]):
                                            btn.click()
                                            print(f"✅ Кликнул кнопку")
                                            time.sleep(3)
                                    except:
                                        continue
                            except:
                                pass
                        
                        # Извлекаем через JS
                        print("🔍 Извлекаю отзывы через JavaScript...")
                        js = """
                        const reviews = [];
                        const selectors = [
                            '[data-widget="webReview"]',
                            'article[class*="review"]',
                            '[class*="review-item"]'
                        ];
                        
                        let items = [];
                        for (let sel of selectors) {
                            items.push(...document.querySelectorAll(sel));
                        }
                        items = Array.from(new Set(items));
                        
                        items.forEach(item => {
                            const text = (item.innerText || item.textContent || '').trim();
                            if (text.length < 30) return;
                            if (text.toLowerCase().includes('cookie') || text.toLowerCase().includes('политика')) return;
                            
                            const author = item.querySelector('strong, b, [class*="author"]')?.innerText?.trim() || 'Аноним';
                            const stars = item.querySelectorAll('[class*="star"][class*="fill"], [class*="star"].active').length || 0;
                            
                            if (text.length > 20) {
                                reviews.push({author: author.length > 50 ? 'Аноним' : author, rating: stars, text: text});
                            }
                        });
                        return reviews;
                        """
                        
                        result = page.evaluate(js)
                        print(f"📊 JavaScript нашел {len(result) if result else 0} элементов")
                        
                        seen_texts = set()
                        reviews_list = []
                        for item in (result or []):
                            text = item.get('text', '').strip()
                            if not text or len(text) < 20:
                                continue
                            
                            # Проверка дубликатов
                            text_hash = hash(text[:100])
                            if text_hash in seen_texts:
                                continue
                            seen_texts.add(text_hash)
                            
                            reviews_list.append({
                                "author": item.get('author', 'Аноним'),
                                "rating": item.get('rating', 0),
                                "text": text,
                                "date": datetime.now()
                            })
                        
                        browser.close()
                        print("📝 [THREAD] Браузер закрыт, возвращаю результаты...")
                        return reviews_list
                except Exception as e:
                    print(f"📝 [THREAD] Ошибка в потоке Ozon: {e}")
                    import traceback
                    print(traceback.format_exc())
                    return []
            
            print("📝 [MAIN] Запускаю ThreadPoolExecutor для Ozon...")
            import sys
            sys.stdout.flush()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                print("📝 [MAIN] Отправляю задачу в поток...")
                sys.stdout.flush()
                future = executor.submit(_playwright_parse)
                print("📝 [MAIN] Ожидаю результат (таймаут 300 сек)...")
                sys.stdout.flush()
                try:
                    reviews = future.result(timeout=300)
                    print(f"📝 [MAIN] Получен результат: {len(reviews) if reviews else 0} отзывов")
                    sys.stdout.flush()
                except concurrent.futures.TimeoutError:
                    print("❌ [MAIN] Таймаут при ожидании результата!")
                    sys.stdout.flush()
                    reviews = []
                except Exception as e:
                    print(f"❌ [MAIN] Ошибка при получении результата: {e}")
                    sys.stdout.flush()
                    reviews = []
                
                if reviews:
                    print(f"✅ Найдено {len(reviews)} отзывов")
        except Exception as e:
            print(f"❌ Ошибка Ozon: {e}")
            import traceback
            print(traceback.format_exc())
        
        return reviews


class SimpleYandexMarketParser(BaseParser):
    """Простой парсер Яндекс.Маркет с Playwright"""
    
    def __init__(self):
        super().__init__()
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        match = re.search(r'/card/[^/]+/(\d+)(?:\?|$)', url)
        if match:
            return match.group(1)
        match = re.search(r'/product/(\d+)(?:/|\?|$)', url)
        return match.group(1) if match else None
    
    def get_product_name(self, url: str) -> Optional[str]:
        try:
            def _get_name():
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                    )
                    page = browser.new_page()
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    time.sleep(2)
                    h1 = page.query_selector('h1')
                    name = h1.inner_text().strip() if h1 else None
                    browser.close()
                    return name
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_get_name)
                return future.result(timeout=60)
        except:
            return None
    
    def parse_reviews(self, url: str) -> List[Dict]:
        product_id = self._extract_product_id(url)
        if not product_id:
            print(f"❌ Не удалось извлечь ID товара из URL: {url}")
            return []
        
        print(f"🔍 Извлечен ID товара: {product_id}")
        print("🚀 Запускаю Playwright для Яндекс.Маркет...")
        
        reviews = []
        try:
            def _playwright_parse():
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                    )
                    page = browser.new_page()
                    page.set_viewport_size({"width": 1920, "height": 1080})
                    
                    # Пробуем найти slug из URL
                    slug_match = re.search(r'/card/([^/]+)/', url)
                    slug = slug_match.group(1) if slug_match else ''
                    
                    if slug:
                        review_url = f"https://market.yandex.ru/card/{slug}/{product_id}/reviews"
                    else:
                        review_url = f"https://market.yandex.ru/product/{product_id}/reviews"
                    
                    print(f"🌐 Открываю страницу отзывов: {review_url}")
                    page.goto(review_url, wait_until="networkidle", timeout=30000)
                    time.sleep(3)
                    
                    print("📜 Прокручиваю страницу...")
                    for i in range(15):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(2)
                        
                        # Ищем кнопки "Показать еще"
                        try:
                            buttons = page.query_selector_all("button")
                            for btn in buttons:
                                try:
                                    text = btn.inner_text().lower()
                                    if any(word in text for word in ["показать", "еще", "загрузить"]):
                                        btn.click()
                                        print(f"✅ Кликнул кнопку")
                                        time.sleep(3)
                                except:
                                    continue
                        except:
                            pass
                    
                    # Извлекаем через JS
                    print("🔍 Извлекаю отзывы через JavaScript...")
                    js = """
                    const reviews = [];
                    const selectors = [
                        '[class*="review"]',
                        'article[class*="review"]',
                        '[data-review-id]'
                    ];
                    
                    let items = [];
                    for (let sel of selectors) {
                        items.push(...document.querySelectorAll(sel));
                    }
                    items = Array.from(new Set(items));
                    
                    items.forEach(item => {
                        const text = (item.innerText || item.textContent || '').trim();
                        if (text.length < 30) return;
                        if (text.toLowerCase().includes('cookie') || text.toLowerCase().includes('политика')) return;
                        
                        const author = item.querySelector('strong, b, [class*="author"]')?.innerText?.trim() || 'Аноним';
                        const stars = item.querySelectorAll('[class*="star"][class*="fill"], [class*="star"].active').length || 0;
                        
                        if (text.length > 20) {
                            reviews.push({author: author.length > 50 ? 'Аноним' : author, rating: stars, text: text});
                        }
                    });
                    return reviews;
                    """
                    
                    result = page.evaluate(js)
                    print(f"📊 JavaScript нашел {len(result) if result else 0} элементов")
                    
                    seen_texts = set()
                    reviews_list = []
                    for item in (result or []):
                        text = item.get('text', '').strip()
                        if not text or len(text) < 20:
                            continue
                        
                        # Проверка дубликатов
                        text_hash = hash(text[:100])
                        if text_hash in seen_texts:
                            continue
                        seen_texts.add(text_hash)
                        
                        reviews_list.append({
                            "author": item.get('author', 'Аноним'),
                            "rating": item.get('rating', 0),
                            "text": text,
                            "date": datetime.now()
                        })
                    
                    browser.close()
                    return reviews_list
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_playwright_parse)
                reviews = future.result(timeout=300)
                
                if reviews:
                    print(f"✅ Найдено {len(reviews)} отзывов")
        except Exception as e:
            print(f"❌ Ошибка Яндекс.Маркет: {e}")
            import traceback
            print(traceback.format_exc())
        
        return reviews
