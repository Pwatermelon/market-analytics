"""
Парсер для Яндекс.Маркета с обходом капч и блокировок
"""
from typing import List, Dict, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
import time
import random
from .base_parser import BaseParser


class YandexMarketParser(BaseParser):
    """Парсер для Яндекс.Маркета с использованием Selenium"""
    
    def __init__(self):
        super().__init__()
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """Инициализация браузера с обходом детекции"""
        try:
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument(f'user-agent={self.ua.random}')
            
            # Используем undetected-chromedriver для обхода детекции
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Ошибка инициализации драйвера: {e}")
            # Fallback на обычный Chrome
            try:
                options = Options()
                options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                self.driver = webdriver.Chrome(options=options)
            except Exception as e2:
                print(f"Не удалось инициализировать Chrome: {e2}")
                self.driver = None
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        """Извлечение ID товара из URL"""
        # Яндекс.Маркет URL форматы:
        # https://market.yandex.ru/card/название-товара/4483801276?параметры
        # https://market.yandex.ru/product/12345678
        # https://yandex.ru/market/product/12345678
        # https://market.yandex.ru/product/название-товара-12345678
        
        # Основной формат: /card/название/ID?параметры
        # ID находится после последнего / перед ?
        match = re.search(r'/card/[^/]+/(\d+)(?:\?|$)', url)
        if match:
            return match.group(1)
        
        # Формат /product/...-12345678
        match = re.search(r'/product/[^/]+-(\d+)(?:/|\?|$)', url)
        if match:
            return match.group(1)
        
        # Простой формат: /product/12345678
        match = re.search(r'/product/(\d+)(?:/|\?|$)', url)
        if match:
            return match.group(1)
        
        return None
    
    def _wait_for_page_load(self, timeout: int = 30):
        """Ожидание загрузки страницы"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            time.sleep(2)  # Дополнительная задержка для JavaScript
        except TimeoutException:
            pass
    
    def get_product_name(self, url: str) -> Optional[str]:
        """Получение названия товара"""
        if not self.driver:
            return None
        
        try:
            self.driver.get(url)
            self._wait_for_page_load()
            
            # Пробуем разные селекторы для названия
            selectors = [
                'h1[data-auto="title"]',
                'h1[data-zone-name="productTitle"]',
                'h1',
                '.product-title',
                '[data-auto="product-title"]'
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    name = element.text.strip()
                    if name:
                        return name
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"Ошибка получения названия товара: {e}")
            return None
    
    def parse_reviews(self, url: str) -> List[Dict]:
        """Парсинг отзывов с Яндекс.Маркета"""
        if not self.driver:
            return []
        
        reviews = []
        
        try:
            print("🌐 Открываю страницу товара Яндекс.Маркета...")
            self.driver.get(url)
            self._wait_for_page_load()
            time.sleep(5)
            
            # Ищем и переходим на вкладку отзывов
            print("🔍 Ищу вкладку с отзывами...")
            feedback_clicked = False
            
            # Пробуем найти вкладку "Отзывы"
            tab_selectors = [
                'a[href*="reviews"]',
                'a[href*="отзыв"]',
                'button[data-auto*="reviews"]',
                '[data-zone-name*="reviews"]',
                'a:contains("Отзывы")',
                'button:contains("Отзывы")'
            ]
            
            for selector in tab_selectors:
                try:
                    tabs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for tab in tabs:
                        tab_text = tab.text.lower()
                        tab_href = tab.get_attribute("href") or ""
                        if "отзыв" in tab_text or "review" in tab_text or "reviews" in tab_href.lower():
                            print(f"✅ Нашел вкладку отзывов: {tab.text}")
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
                            time.sleep(1)
                            self.driver.execute_script("arguments[0].click();", tab)
                            time.sleep(5)
                            feedback_clicked = True
                            break
                    if feedback_clicked:
                        break
                except:
                    continue
            
            # Если не нашли вкладку, пробуем перейти напрямую на страницу отзывов
            if not feedback_clicked:
                print("🔄 Пробую перейти на страницу отзывов напрямую...")
                product_id = self._extract_product_id(url)
                if product_id:
                    # Для формата /card/.../ID используем другой URL
                    if '/card/' in url:
                        # Извлекаем slug из URL
                        slug_match = re.search(r'/card/([^/]+)/', url)
                        slug = slug_match.group(1) if slug_match else ''
                        review_urls = [
                            f"https://market.yandex.ru/card/{slug}/{product_id}/reviews",
                            f"https://market.yandex.ru/product/{product_id}/reviews",
                        ]
                    else:
                        review_urls = [
                            f"https://market.yandex.ru/product/{product_id}/reviews",
                            f"https://yandex.ru/market/product/{product_id}/reviews",
                            f"{url}/reviews"
                        ]
                    
                    for review_url in review_urls:
                        try:
                            print(f"🔗 Пробую URL: {review_url}")
                            self.driver.get(review_url)
                            self._wait_for_page_load()
                            time.sleep(5)
                            print(f"✅ Перешел на страницу отзывов")
                            break
                        except:
                            continue
            
            # Прокручиваем и загружаем отзывы
            print("📜 Прокручиваю страницу для загрузки отзывов...")
            last_review_count = 0
            no_change_iterations = 0
            
            for i in range(20):
                # Прокручиваем вниз
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Ждем загрузки
                time.sleep(1)
                
                # Проверяем количество отзывов
                current_count = self.driver.execute_script("""
                    return document.querySelectorAll('[class*="review"], [class*="отзыв"], [data-auto*="review"]').length;
                """)
                
                if current_count > last_review_count:
                    last_review_count = current_count
                    no_change_iterations = 0
                    print(f"📊 Найдено элементов отзывов: {current_count}")
                else:
                    no_change_iterations += 1
                
                # Ищем кнопки "Показать еще"
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        try:
                            if not btn.is_displayed():
                                continue
                            btn_text = btn.text.lower()
                            if any(word in btn_text for word in ["показать", "загрузить", "еще", "more", "ещё"]):
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                time.sleep(0.5)
                                self.driver.execute_script("arguments[0].click();", btn)
                                print(f"✅ Кликнул: {btn.text}")
                                time.sleep(4)
                                no_change_iterations = 0
                        except:
                            continue
                except:
                    pass
                
                if no_change_iterations >= 5:
                    print("✅ Загрузка завершена")
                    break
            
            # Парсим отзывы
            print("🔍 Парсю отзывы из HTML...")
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            reviews = self._parse_from_html(soup)
            
            # Если не нашли, пробуем через JavaScript
            if len(reviews) == 0:
                print("🔄 Пробую извлечь через JavaScript...")
                reviews = self._extract_reviews_via_js()
            
            print(f"✅ Итого найдено отзывов: {len(reviews)}")
            
        except Exception as e:
            print(f"❌ Ошибка парсинга отзывов Яндекс.Маркета: {e}")
            import traceback
            print(traceback.format_exc())
        
        return reviews
    
    def _extract_reviews_via_js(self) -> List[Dict]:
        """Извлечение отзывов через JavaScript"""
        reviews = []
        try:
            js_code = """
            (function() {
                const reviews = [];
                
                const selectors = [
                    '[class*="review"]',
                    '[data-auto*="review"]',
                    '[class*="отзыв"]',
                    'article',
                    '[data-zone-name*="review"]'
                ];
                
                let elements = [];
                for (let selector of selectors) {
                    try {
                        const found = document.querySelectorAll(selector);
                        elements.push(...Array.from(found));
                    } catch(e) {}
                }
                
                elements = Array.from(new Set(elements));
                
                for (let elem of elements) {
                    try {
                        const text = elem.innerText || elem.textContent || '';
                        if (text.length < 30) continue;
                        
                        if (text.toLowerCase().includes('cookie') || 
                            text.toLowerCase().includes('политика')) continue;
                        
                        let author = 'Аноним';
                        const authorElem = elem.querySelector('[class*="author"], [class*="user"], strong, b');
                        if (authorElem) {
                            author = (authorElem.innerText || authorElem.textContent || '').trim();
                            if (author.length > 50) author = 'Аноним';
                        }
                        
                        let rating = 0;
                        const stars = elem.querySelectorAll('[class*="star"], [class*="rating"]');
                        if (stars.length > 0) {
                            rating = stars.length;
                        }
                        
                        let dateText = '';
                        const dateElem = elem.querySelector('time, [class*="date"]');
                        if (dateElem) {
                            dateText = dateElem.getAttribute('datetime') || dateElem.innerText || '';
                        }
                        
                        let cleanText = text;
                        const lines = cleanText.split('\\n');
                        cleanText = lines.filter(line => {
                            line = line.trim();
                            return line.length > 10 && 
                                   !line.toLowerCase().includes('отзыв') &&
                                   !line.toLowerCase().includes('оценка');
                        }).join(' ').trim();
                        
                        if (cleanText.length > 20) {
                            reviews.push({
                                author: author,
                                rating: rating,
                                text: cleanText,
                                date: dateText || new Date().toISOString()
                            });
                        }
                    } catch(e) {}
                }
                
                return reviews;
            })();
            """
            
            result = self.driver.execute_script(js_code)
            if result:
                for item in result:
                    try:
                        date = datetime.now()
                        if item.get('date'):
                            date = self._parse_date(item['date'])
                        
                        reviews.append({
                            "author": item.get('author', 'Аноним'),
                            "rating": item.get('rating', 0),
                            "text": item.get('text', ''),
                            "date": date
                        })
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ Ошибка JavaScript извлечения: {e}")
        
        return reviews
    
    def _parse_from_html(self, soup: BeautifulSoup) -> List[Dict]:
        """Парсинг отзывов из HTML"""
        reviews = []
        
        # Селекторы для Яндекс.Маркета
        review_selectors = [
            '[class*="review"]',
            '[data-auto*="review"]',
            '[class*="отзыв"]',
            'article[class*="review"]',
            '[data-zone-name*="review"]'
        ]
        
        review_containers = []
        for selector in review_selectors:
            try:
                elements = soup.select(selector)
                review_containers.extend(elements)
            except:
                continue
        
        print(f"🔍 Найдено {len(review_containers)} потенциальных контейнеров отзывов")
        
        seen_texts = set()
        for container in review_containers:
            try:
                text = container.get_text(separator=' ', strip=True)
                
                if len(text) < 30:
                    continue
                
                # Очищаем текст
                lines = text.split('\n')
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    if len(line) > 15 and not any(skip in line.lower() for skip in ['отзыв', 'оценка', 'рейтинг', 'cookie']):
                        clean_lines.append(line)
                
                review_text = ' '.join(clean_lines)
                
                if len(review_text) < 20:
                    continue
                
                # Проверяем дубликаты
                text_hash = hash(review_text[:100])
                if text_hash in seen_texts:
                    continue
                seen_texts.add(text_hash)
                
                # Автор
                author = "Аноним"
                author_elem = container.find(['strong', 'b', 'span'], class_=lambda x: x and ('author' in str(x).lower() or 'user' in str(x).lower()))
                if not author_elem:
                    author_elem = container.find(['strong', 'b'])
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    if len(author) > 50:
                        author = "Аноним"
                
                # Рейтинг
                rating = 0
                stars = container.find_all(['span', 'div', 'i'], class_=lambda x: x and 'star' in str(x).lower())
                if stars:
                    rating = len([s for s in stars if 'fill' in str(s.get('class', [])).lower() or 'active' in str(s.get('class', [])).lower()])
                
                if not rating:
                    rating_match = re.search(r'(\d+)\s*(звезд|star|⭐)', container.get_text(), re.IGNORECASE)
                    if rating_match:
                        rating = int(rating_match.group(1))
                
                # Дата
                date = datetime.now()
                date_elem = container.find(['time', 'span', 'div'], class_=lambda x: x and 'date' in str(x).lower())
                if not date_elem:
                    date_elem = container.find('time')
                if date_elem:
                    date_text = date_elem.get_text(strip=True) or date_elem.get('datetime', '')
                    if date_text:
                        date = self._parse_date(date_text)
                
                reviews.append({
                    "author": author,
                    "rating": rating,
                    "text": review_text,
                    "date": date
                })
                
            except Exception as e:
                print(f"⚠️ Ошибка парсинга контейнера: {e}")
                continue
        
        print(f"✅ Распарсено {len(reviews)} уникальных отзывов")
        return reviews
    
    def _parse_date(self, date_text: str) -> datetime:
        """Парсинг даты из текста"""
        try:
            patterns = [
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 26.11.2024
                r'(\d{4})-(\d{2})-(\d{2})',  # 2024-11-26
                r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})',
            ]
            
            months = {
                'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
            }
            
            for pattern in patterns:
                match = re.search(pattern, date_text.lower())
                if match:
                    if len(match.groups()) == 3:
                        if match.group(2) in months:
                            day, month_name, year = match.groups()
                            month = months[month_name]
                            return datetime(int(year), month, int(day))
                        else:
                            parts = list(match.groups())
                            if len(parts[0]) == 4:  # YYYY-MM-DD
                                return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                            else:  # DD.MM.YYYY
                                return datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        except:
            pass
        
        return datetime.now()
    
    def __del__(self):
        """Закрытие браузера при удалении объекта"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

