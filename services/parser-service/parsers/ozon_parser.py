"""
Улучшенный парсер для Ozon с обходом капч и блокировок
"""
from typing import List, Dict, Optional
from datetime import datetime
import re
import json
import time
try:
    import requests
except ImportError:
    requests = None
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from .base_parser import BaseParser


class OzonParser(BaseParser):
    """Парсер для Ozon"""
    
    def __init__(self):
        super().__init__()
        self.driver = None
        self.session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': self.ua.random,
                'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            })
        self._init_driver()
    
    def _init_driver(self):
        """Инициализация браузера"""
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
            
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Ошибка инициализации драйвера Ozon: {e}")
            self.driver = None
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        """Извлечение ID товара из URL"""
        # Ozon URL форматы:
        # https://www.ozon.ru/product/142895313
        # https://www.ozon.ru/product/142895313/
        # https://www.ozon.ru/product/название-товара-142895313/
        # https://ozon.ru/product/название-товара-142895313/?at=...
        
        # Сначала пробуем простой формат: /product/123456789
        match = re.search(r'/product/(\d+)(?:/|\?|$)', url)
        if match:
            return match.group(1)
        
        # Если не нашли, пробуем формат с названием: /product/...-142895313/
        match = re.search(r'/product/[^/]+-(\d+)(?:/|\?|$)', url)
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
            time.sleep(3)
            
            selectors = [
                'h1[data-widget="webProductHeading"]',
                'h1',
                '.product-page__title',
                '[data-widget="webProductHeading"]'
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
            print(f"Ошибка получения названия Ozon: {e}")
            return None
    
    def parse_reviews(self, url: str) -> List[Dict]:
        """Парсинг отзывов с Ozon - сначала пробуем API, потом Selenium"""
        product_id = self._extract_product_id(url)
        if not product_id:
            print("❌ Не удалось извлечь ID товара из URL")
            return []
        
        # Пробуем через API отзывов
        api_reviews = self._try_api_method(product_id)
        if api_reviews and len(api_reviews) > 0:
            print(f"✅ API метод вернул {len(api_reviews)} отзывов")
            return api_reviews
        
        # Если API не сработал, используем Selenium
        print("🔄 API не сработал, переключаюсь на Selenium...")
        return self._parse_with_selenium(url, product_id)
    
    def _try_api_method(self, product_id: str) -> List[Dict]:
        """Попытка получить отзывы через API"""
        reviews = []
        
        if not self.session or not requests:
            return reviews
        
        try:
            # Пробуем получить отзывы через неофициальный API Ozon
            api_url = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"
            
            # Параметры для запроса отзывов
            params = {
                'url': f'/product/{product_id}/',
                'layoutContainer': 'webReviewList',
                'page': 1
            }
            
            headers = {
                'Referer': f'https://www.ozon.ru/product/{product_id}/',
                'Accept': 'application/json',
            }
            
            response = self.session.get(api_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Парсим структуру ответа Ozon (может отличаться)
                    if 'widgetStates' in data:
                        # Пробуем найти отзывы в структуре
                        for widget in data.get('widgetStates', []):
                            if 'review' in str(widget).lower() or 'feedback' in str(widget).lower():
                                # Парсим отзывы из виджета
                                pass
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"⚠️ API метод не сработал: {e}")
        
        return reviews
    
    def _parse_with_selenium(self, url: str, product_id: str) -> List[Dict]:
        """Парсинг через Selenium"""
        if not self.driver:
            return []
        
        reviews = []
        
        try:
            print("🌐 Открываю страницу товара Ozon...")
            self.driver.get(url)
            self._wait_for_page_load()
            time.sleep(5)
            
            # Ищем и переходим на вкладку отзывов
            print("🔍 Ищу вкладку с отзывами...")
            feedback_clicked = False
            
            # Пробуем найти вкладку "Отзывы" разными способами
            tab_selectors = [
                'a[href*="reviews"]',
                'a[href*="отзыв"]',
                'button[data-widget*="review"]',
                '[data-widget="webReviews"]',
                'a:contains("Отзывы")',
                'button:contains("Отзывы")',
                '[aria-label*="Отзывы"]',
                '[aria-label*="отзыв"]'
            ]
            
            # Пробуем найти все кликабельные элементы
            all_clickable = self.driver.find_elements(By.CSS_SELECTOR, "a, button, div[role='button'], span[role='button']")
            
            for element in all_clickable:
                try:
                    text = element.text.lower()
                    href = element.get_attribute("href") or ""
                    aria_label = element.get_attribute("aria-label") or ""
                    data_widget = element.get_attribute("data-widget") or ""
                    
                    # Ищем по ключевым словам
                    if any(word in text for word in ["отзыв", "review", "отзывы", "reviews"]) or \
                       "review" in href.lower() or "отзыв" in href.lower() or \
                       "review" in aria_label.lower() or "review" in data_widget.lower():
                        print(f"🎯 Нашел потенциальную вкладку: {element.text[:50]} | href={href[:50]}")
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(1)
                            self.driver.execute_script("arguments[0].click();", element)
                            print("✅ Кликнул на вкладку отзывов")
                            time.sleep(5)
                            feedback_clicked = True
                            break
                        except Exception as e:
                            print(f"⚠️ Не удалось кликнуть: {e}")
                            continue
                except:
                    continue
            
            # Если не нашли вкладку, пробуем перейти напрямую на страницу отзывов
            if not feedback_clicked:
                print("🔄 Пробую перейти на страницу отзывов напрямую...")
                review_urls = [
                    f"https://www.ozon.ru/product/{product_id}/reviews/",
                    f"https://www.ozon.ru/product/{product_id}/#reviews",
                    f"{url}#reviews",
                    f"{url}reviews/"
                ]
                
                for review_url in review_urls:
                    try:
                        print(f"🔗 Пробую URL: {review_url}")
                        self.driver.get(review_url)
                        self._wait_for_page_load()
                        time.sleep(5)
                        
                        # Проверяем, есть ли отзывы на странице
                        page_text = self.driver.page_source.lower()
                        if "отзыв" in page_text or "review" in page_text:
                            print(f"✅ Перешел на страницу отзывов: {review_url}")
                            break
                    except Exception as e:
                        print(f"⚠️ Ошибка при переходе на {review_url}: {e}")
                        continue
            
            # Прокручиваем страницу для загрузки отзывов
            print("📜 Прокручиваю страницу для загрузки отзывов...")
            last_review_count = 0
            no_change_iterations = 0
            
            for i in range(20):
                # Прокручиваем вниз
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Ждем загрузки
                time.sleep(1)
                
                # Проверяем количество отзывов через JS
                current_count = self.driver.execute_script("""
                    return document.querySelectorAll('[data-widget="webReview"], [class*="review"], [data-review-id]').length;
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
                            if any(word in btn_text for word in ["показать", "загрузить", "еще", "more", "ещё", "показать еще"]):
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
            
            # Пробуем извлечь отзывы через JavaScript
            print("🔍 Пробую извлечь отзывы через JavaScript...")
            js_reviews = self._extract_reviews_via_js()
            if js_reviews:
                print(f"✅ JavaScript метод нашел {len(js_reviews)} отзывов")
                reviews = js_reviews
            else:
                # Парсим отзывы из HTML
                print("🔍 Парсю отзывы из HTML...")
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                reviews = self._parse_from_html(soup)
            
            print(f"✅ Итого найдено отзывов: {len(reviews)}")
            
        except Exception as e:
            print(f"❌ Ошибка парсинга отзывов Ozon: {e}")
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
                
                // Ищем все возможные контейнеры отзывов Ozon
                const selectors = [
                    '[data-widget="webReview"]',
                    '[class*="review"]',
                    '[data-review-id]',
                    '[class*="ozon-review"]',
                    'article[class*="review"]'
                ];
                
                let elements = [];
                for (let selector of selectors) {
                    try {
                        const found = document.querySelectorAll(selector);
                        elements.push(...Array.from(found));
                    } catch(e) {}
                }
                
                // Убираем дубликаты
                elements = Array.from(new Set(elements));
                
                for (let elem of elements) {
                    try {
                        const text = elem.innerText || elem.textContent || '';
                        
                        // Пропускаем слишком короткие
                        if (text.length < 30) continue;
                        
                        // Пропускаем служебные
                        if (text.toLowerCase().includes('cookie') || 
                            text.toLowerCase().includes('политика') ||
                            text.toLowerCase().includes('согласие')) continue;
                        
                        // Ищем автора
                        let author = 'Аноним';
                        const authorElem = elem.querySelector('[class*="author"], [class*="user"], strong, b, [class*="name"]');
                        if (authorElem) {
                            author = (authorElem.innerText || authorElem.textContent || '').trim();
                            if (author.length > 50) author = 'Аноним';
                        }
                        
                        // Ищем рейтинг
                        let rating = 0;
                        const stars = elem.querySelectorAll('[class*="star"], [class*="rating"], [data-rating]');
                        if (stars.length > 0) {
                            // Пробуем извлечь из data-rating
                            for (let star of stars) {
                                const dataRating = star.getAttribute('data-rating');
                                if (dataRating) {
                                    rating = parseInt(dataRating);
                                    break;
                                }
                            }
                            if (!rating) {
                                // Считаем заполненные звезды
                                const filled = Array.from(stars).filter(s => 
                                    s.classList.contains('filled') || 
                                    s.classList.contains('active') ||
                                    s.style.color === 'gold' ||
                                    s.style.color === '#ffc107'
                                );
                                rating = filled.length;
                            }
                        }
                        
                        // Ищем дату
                        let dateText = '';
                        const dateElem = elem.querySelector('time, [class*="date"], [datetime]');
                        if (dateElem) {
                            dateText = dateElem.getAttribute('datetime') || dateElem.innerText || '';
                        }
                        
                        // Очищаем текст от служебной информации
                        let cleanText = text;
                        const lines = cleanText.split('\\n');
                        cleanText = lines.filter(line => {
                            line = line.trim();
                            return line.length > 10 && 
                                   !line.toLowerCase().includes('отзыв') &&
                                   !line.toLowerCase().includes('оценка') &&
                                   !line.toLowerCase().includes('рейтинг');
                        }).join(' ').trim();
                        
                        if (cleanText.length > 20) {
                            reviews.push({
                                author: author,
                                rating: rating,
                                text: cleanText,
                                date: dateText || new Date().toISOString()
                            });
                        }
                    } catch(e) {
                        console.error('Error parsing element:', e);
                    }
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
        seen_texts = set()
        
        # Селекторы для Ozon
        review_selectors = [
            '[data-widget="webReview"]',
            '[class*="review"]',
            '[data-review-id]',
            '[class*="ozon-review"]',
            'article[class*="review"]'
        ]
        
        review_containers = []
        for selector in review_selectors:
            try:
                elements = soup.select(selector)
                review_containers.extend(elements)
            except:
                continue
        
        print(f"🔍 Найдено {len(review_containers)} потенциальных контейнеров отзывов")
        
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
                author_elem = container.find(['strong', 'b', 'span'], class_=lambda x: x and ('author' in str(x).lower() or 'user' in str(x).lower() or 'name' in str(x).lower()))
                if not author_elem:
                    author_elem = container.find(['strong', 'b'])
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    if len(author) > 50:
                        author = "Аноним"
                
                # Рейтинг
                rating = 0
                # Ищем data-rating атрибут
                rating_attr = container.get('data-rating')
                if rating_attr:
                    try:
                        rating = int(rating_attr)
                    except:
                        pass
                
                # Ищем звезды
                if not rating:
                    stars = container.find_all(['span', 'div', 'i'], class_=lambda x: x and 'star' in str(x).lower())
                    if stars:
                        filled = [s for s in stars if 'fill' in str(s.get('class', [])).lower() or 'active' in str(s.get('class', [])).lower()]
                        rating = len(filled)
                
                # Ищем число рейтинга в тексте
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
        """Парсинг даты"""
        try:
            # Форматы: "26 ноября 2024", "26.11.2024", "2024-11-26", ISO format
            patterns = [
                r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})',
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
                r'(\d{4})-(\d{2})-(\d{2})',
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
            
            # Пробуем ISO формат
            try:
                return datetime.fromisoformat(date_text.replace('Z', '+00:00'))
            except:
                pass
        except:
            pass
        
        return datetime.now()
    
    def __del__(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

