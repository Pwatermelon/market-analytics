"""
Улучшенный парсер для Wildberries - использует API и Selenium
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from .base_parser import BaseParser


class WildberriesParser(BaseParser):
    """Парсер для Wildberries с использованием Selenium"""
    
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
    
    def _extract_article(self, url: str) -> Optional[str]:
        """Извлечение артикула из URL"""
        # Форматы: 
        # /catalog/12345678/detail.aspx
        # /catalog/12345678/
        # /catalog/12345678
        match = re.search(r'/catalog/(\d+)(?:/|$)', url)
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
    
    def _scroll_to_load_reviews(self, max_scrolls: int = 5):
        """Прокрутка страницы для загрузки отзывов"""
        for _ in range(max_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2))
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
    
    def get_product_name(self, url: str) -> Optional[str]:
        """Получение названия товара"""
        if not self.driver:
            return None
        
        try:
            self.driver.get(url)
            self._wait_for_page_load()
            
            # Пробуем разные селекторы для названия
            selectors = [
                'h1.product-page__title',
                'h1[data-link="text{:product^goodsName}"]',
                'h1',
                '.product-page__header h1',
                '[data-link="text{:product^goodsName}"]'
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
        """Парсинг отзывов - сначала пробуем API, потом Selenium"""
        article = self._extract_article(url)
        if not article:
            print("❌ Не удалось извлечь артикул из URL")
            return []
        
        # Пробуем через API отзывов
        api_reviews = self._try_api_method(article)
        if api_reviews and len(api_reviews) > 0:
            print(f"✅ API метод вернул {len(api_reviews)} отзывов")
            return api_reviews
        
        # Если API не сработал, используем Selenium
        print("🔄 API не сработал, переключаюсь на Selenium...")
        return self._parse_with_selenium(url, article)
    
    def _try_api_method(self, article: str) -> List[Dict]:
        """Попытка получить отзывы через API"""
        reviews = []
        
        if not self.session or not requests:
            return reviews
        
        try:
            # Пробуем получить отзывы через неофициальный API
            api_url = "https://feedbacks1.wildberries.ru/api/v1/summary/full"
            
            params = {
                'nmId': article,
                'skip': 0,
                'take': 100
            }
            
            headers = {
                'Referer': f'https://www.wildberries.ru/catalog/{article}/detail.aspx'
            }
            
            response = self.session.get(api_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'feedbacks' in data:
                        for feedback in data['feedbacks']:
                            try:
                                review_text = feedback.get('text', '')
                                if not review_text or len(review_text) < 10:
                                    continue
                                
                                # Парсим дату
                                date_str = feedback.get('createdDate', '')
                                date = datetime.now()
                                if date_str:
                                    try:
                                        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                    except:
                                        pass
                                
                                reviews.append({
                                    "author": feedback.get('wbUserDetails', {}).get('name', 'Аноним'),
                                    "rating": feedback.get('productValuation', 0),
                                    "text": review_text,
                                    "date": date
                                })
                            except Exception as e:
                                print(f"⚠️ Ошибка парсинга отзыва из API: {e}")
                                continue
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"⚠️ API метод не сработал: {e}")
        
        return reviews
    
    def _parse_with_selenium(self, url: str, article: str) -> List[Dict]:
        """Парсинг через Selenium"""
        if not self.driver:
            return []
        
        reviews = []
        
        try:
            # Переходим на страницу отзывов
            feedback_url = f"https://www.wildberries.ru/catalog/{article}/feedbacks"
            print(f"🌐 Открываю страницу отзывов: {feedback_url}")
            
            self.driver.get(feedback_url)
            self._wait_for_page_load()
            time.sleep(5)
            
            # Прокручиваем страницу
            print("📜 Прокручиваю страницу...")
            for i in range(10):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Ищем кнопки "Показать еще"
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        try:
                            if not btn.is_displayed():
                                continue
                            btn_text = btn.text.lower()
                            if any(word in btn_text for word in ["показать", "загрузить", "еще", "ещё"]):
                                self.driver.execute_script("arguments[0].click();", btn)
                                print(f"✅ Кликнул: {btn.text}")
                                time.sleep(3)
                        except:
                            continue
                except:
                    pass
            
            # Парсим HTML
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            reviews = self._parse_html_reviews(soup)
            
            print(f"✅ Найдено отзывов: {len(reviews)}")
            
        except Exception as e:
            print(f"❌ Ошибка парсинга через Selenium: {e}")
            import traceback
            print(traceback.format_exc())
        
        return reviews
    
    def _parse_html_reviews(self, soup: BeautifulSoup) -> List[Dict]:
        """Парсинг отзывов из HTML"""
        reviews = []
        seen_texts = set()
        
        # Ищем все возможные контейнеры отзывов
        selectors = [
            'div[class*="feedback"]',
            'div[class*="review"]',
            'div[class*="comment"]',
            '[data-feedback-id]',
            'article',
            '.feedback-item',
            '.review-item'
        ]
        
        containers = []
        for selector in selectors:
            try:
                elements = soup.select(selector)
                containers.extend(elements)
            except:
                continue
        
        print(f"🔍 Найдено {len(containers)} потенциальных контейнеров")
        
        for container in containers:
            try:
                text = container.get_text(separator=' ', strip=True)
                
                if len(text) < 30:
                    continue
                
                # Очищаем от служебной информации
                lines = text.split('\n')
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    if len(line) > 15 and not any(skip in line.lower() for skip in 
                        ['отзыв', 'оценка', 'рейтинг', 'cookie', 'политика', 'согласие']):
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
                author_elem = container.find(['strong', 'b', 'span'], 
                    class_=lambda x: x and ('author' in str(x).lower() or 'user' in str(x).lower()))
                if not author_elem:
                    author_elem = container.find(['strong', 'b'])
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    if len(author) > 50:
                        author = "Аноним"
                
                # Рейтинг
                rating = 0
                stars = container.find_all(['span', 'div', 'i'], 
                    class_=lambda x: x and 'star' in str(x).lower())
                if stars:
                    filled = [s for s in stars if 'fill' in str(s.get('class', [])).lower() 
                             or 'active' in str(s.get('class', [])).lower()]
                    rating = len(filled)
                
                if not rating:
                    rating_match = re.search(r'(\d+)\s*(звезд|star|⭐)', container.get_text(), re.IGNORECASE)
                    if rating_match:
                        rating = int(rating_match.group(1))
                
                # Дата
                date = datetime.now()
                date_elem = container.find(['time', 'span', 'div'], 
                    class_=lambda x: x and 'date' in str(x).lower())
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
        
        return reviews
    
    def parse_reviews_old(self, url: str) -> List[Dict]:
        """Парсинг отзывов с Wildberries напрямую со страницы"""
        if not self.driver:
            return []
        
        reviews = []
        
        try:
            print("🌐 Открываю страницу товара...")
            self.driver.get(url)
            self._wait_for_page_load()
            time.sleep(5)  # Даем больше времени на загрузку
            
            # Сохраняем HTML для отладки
            try:
                with open('/tmp/wb_page_before.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("💾 Сохранен HTML страницы в /tmp/wb_page_before.html")
            except:
                pass
            
            # Прокручиваем к началу страницы
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Ищем вкладку "Отзывы" более агрессивно
            print("🔍 Ищу вкладку с отзывами...")
            feedback_clicked = False
            
            # Пробуем найти все возможные элементы, которые могут быть вкладкой отзывов
            all_clickable = self.driver.find_elements(By.CSS_SELECTOR, "a, button, div[role='button'], span[role='button']")
            
            for element in all_clickable:
                try:
                    text = element.text.lower()
                    href = element.get_attribute("href") or ""
                    onclick = element.get_attribute("onclick") or ""
                    data_link = element.get_attribute("data-link") or ""
                    
                    # Ищем по ключевым словам
                    if any(word in text for word in ["отзыв", "feedback", "отзывы", "feedbacks"]) or \
                       "feedback" in href.lower() or "feedback" in onclick.lower() or "feedback" in data_link.lower():
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
                article = self._extract_article(url)
                if article:
                    # Пробуем разные варианты URL отзывов
                    feedback_urls = [
                        f"https://www.wildberries.ru/catalog/{article}/feedbacks",
                        f"https://www.wildberries.ru/catalog/{article}/detail.aspx?tab=feedbacks",
                        f"https://www.wildberries.ru/catalog/{article}/detail.aspx#feedbacks",
                        f"https://www.wildberries.ru/catalog/{article}/detail.aspx?tab=reviews",
                    ]
                    
                    for feedback_url in feedback_urls:
                        try:
                            print(f"🔗 Пробую URL: {feedback_url}")
                            self.driver.get(feedback_url)
                            self._wait_for_page_load()
                            time.sleep(5)
                            
                            # Проверяем, есть ли отзывы на странице
                            page_text = self.driver.page_source.lower()
                            if "отзыв" in page_text or "feedback" in page_text:
                                print(f"✅ Перешел на страницу отзывов: {feedback_url}")
                                break
                        except Exception as e:
                            print(f"⚠️ Ошибка при переходе на {feedback_url}: {e}")
                            continue
            
            # Ждем загрузки динамического контента
            print("⏳ Жду загрузки динамического контента...")
            time.sleep(5)
            
            # Прокручиваем страницу для загрузки отзывов
            print("📜 Прокручиваю страницу для загрузки отзывов...")
            last_review_count = 0
            no_change_iterations = 0
            
            for i in range(20):
                # Прокручиваем вниз
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Ждем загрузки новых элементов
                time.sleep(1)
                
                # Проверяем количество отзывов через JS
                current_count = self.driver.execute_script("""
                    return document.querySelectorAll('[class*="feedback"], [data-feedback-id], article').length;
                """)
                
                if current_count > last_review_count:
                    last_review_count = current_count
                    no_change_iterations = 0
                    print(f"📊 Найдено элементов отзывов: {current_count}")
                else:
                    no_change_iterations += 1
                
                # Ищем и кликаем кнопки загрузки
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
                                no_change_iterations = 0  # Сброс счетчика после клика
                        except:
                            continue
                except:
                    pass
                
                # Если долго не меняется, пробуем прокрутить вверх-вниз
                if no_change_iterations >= 3:
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                # Если 5 раз подряд не изменилось - выходим
                if no_change_iterations >= 5:
                    print("✅ Загрузка завершена (нет новых элементов)")
                    break
            
            # Сохраняем финальный HTML
            try:
                with open('/tmp/wb_page_after.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("💾 Сохранен финальный HTML в /tmp/wb_page_after.html")
            except:
                pass
            
            # Пробуем извлечь отзывы через JavaScript
            print("🔍 Пробую извлечь отзывы через JavaScript...")
            js_reviews = self._extract_reviews_via_js()
            if js_reviews:
                print(f"✅ JavaScript метод нашел {len(js_reviews)} отзывов")
                reviews = js_reviews
            else:
                # Парсим отзывы из HTML
                print("🔍 Парсю отзывы из HTML...")
                page_source = self.driver.page_source
                
                # Выводим статистику страницы для отладки
                print(f"📄 Размер HTML: {len(page_source)} символов")
                print(f"📊 Содержит 'отзыв': {'отзыв' in page_source.lower()}")
                print(f"📊 Содержит 'feedback': {'feedback' in page_source.lower()}")
                
                soup = BeautifulSoup(page_source, 'html.parser')
                reviews = self._parse_from_html_improved(soup)
                
                # Если не нашли, пробуем альтернативный метод
                if len(reviews) == 0:
                    print("🔄 Пробую альтернативный метод парсинга...")
                    reviews = self._parse_alternative_method(soup)
            
            print(f"✅ Итого найдено отзывов: {len(reviews)}")
            
        except Exception as e:
            print(f"❌ Ошибка парсинга отзывов Wildberries: {e}")
            import traceback
            print(traceback.format_exc())
        
        return reviews
    
    
    def _parse_from_html_improved(self, soup: BeautifulSoup) -> List[Dict]:
        """Улучшенный парсинг отзывов - ищет по всем возможным признакам"""
        reviews = []
        
        # Ищем все элементы, которые могут содержать отзывы
        # Пробуем найти по классам, data-атрибутам, структуре
        
        # 1. Ищем по известным классам WB
        review_containers = []
        
        # Различные селекторы для контейнеров отзывов
        container_selectors = [
            'div[class*="feedback"]',
            'div[class*="review"]',
            'div[class*="comment"]',
            'article[class*="feedback"]',
            '[data-feedback-id]',
            '[id*="feedback"]',
            '[id*="review"]'
        ]
        
        for selector in container_selectors:
            try:
                elements = soup.select(selector)
                review_containers.extend(elements)
            except:
                continue
        
        print(f"🔍 Найдено {len(review_containers)} потенциальных контейнеров отзывов")
        
        # 2. Если не нашли по селекторам, ищем по структуре - ищем div с текстом похожим на отзыв
        if not review_containers:
            print("🔍 Ищу отзывы по структуре текста...")
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True)
                # Отзыв обычно содержит несколько предложений
                if len(text) > 50 and text.count('.') >= 1:
                    # Проверяем, нет ли рядом элементов, указывающих на отзыв
                    parent = div.parent
                    if parent:
                        parent_text = parent.get_text(strip=True).lower()
                        if any(word in parent_text for word in ['отзыв', 'feedback', 'оценка', 'рейтинг']):
                            review_containers.append(div)
        
        print(f"📦 Всего найдено {len(review_containers)} потенциальных контейнеров")
        
        # 3. Парсим каждый контейнер
        seen_texts = set()
        for container in review_containers:
            try:
                # Извлекаем текст
                full_text = container.get_text(separator=' ', strip=True)
                
                # Ищем основной текст отзыва (самый длинный параграф)
                paragraphs = container.find_all(['p', 'div', 'span'])
                review_text = ""
                for p in paragraphs:
                    p_text = p.get_text(strip=True)
                    if len(p_text) > len(review_text) and len(p_text) > 30:
                        review_text = p_text
                
                if not review_text or len(review_text) < 20:
                    review_text = full_text
                
                # Убираем служебную информацию
                lines = review_text.split('\n')
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    # Пропускаем короткие строки и служебные
                    if len(line) > 15 and not any(skip in line.lower() for skip in ['отзыв', 'оценка', 'рейтинг', 'звезд', '⭐']):
                        clean_lines.append(line)
                
                review_text = ' '.join(clean_lines)
                
                if len(review_text) < 20:
                    continue
                
                # Проверяем на дубликаты
                text_hash = hash(review_text[:100])
                if text_hash in seen_texts:
                    continue
                seen_texts.add(text_hash)
                
                # Извлекаем автора
                author = "Аноним"
                author_elem = container.find(['strong', 'b', 'span'], class_=lambda x: x and ('author' in str(x).lower() or 'user' in str(x).lower()))
                if not author_elem:
                    author_elem = container.find(['strong', 'b'])
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    if len(author) > 50:  # Слишком длинное - не имя
                        author = "Аноним"
                
                # Извлекаем рейтинг
                rating = 0
                # Ищем звезды
                stars = container.find_all(['span', 'div', 'i'], class_=lambda x: x and 'star' in str(x).lower())
                if stars:
                    rating = len([s for s in stars if 'fill' in str(s.get('class', [])).lower() or 'active' in str(s.get('class', [])).lower()])
                
                # Ищем число рейтинга
                if not rating:
                    rating_match = re.search(r'(\d+)\s*(звезд|star|⭐)', container.get_text(), re.IGNORECASE)
                    if rating_match:
                        rating = int(rating_match.group(1))
                
                # Извлекаем дату
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
    
    def _parse_alternative_method(self, soup: BeautifulSoup) -> List[Dict]:
        """Альтернативный метод - ищем любой текст, похожий на отзыв"""
        reviews = []
        
        print("🔄 Альтернативный метод: ищу любой текст похожий на отзыв...")
        
        # Ищем все элементы с текстом длиннее 50 символов
        all_elements = soup.find_all(['div', 'p', 'span', 'article', 'section'])
        
        for elem in all_elements:
            try:
                text = elem.get_text(separator=' ', strip=True)
                
                # Пропускаем слишком короткие или слишком длинные
                if len(text) < 50 or len(text) > 2000:
                    continue
                
                # Пропускаем служебные тексты
                if any(skip in text.lower() for skip in ['cookie', 'куки', 'согласие', 'политика', 'copyright']):
                    continue
                
                # Ищем элементы, которые могут быть отзывами
                # Отзыв обычно содержит несколько предложений
                sentences = text.split('.')
                if len(sentences) < 2:
                    continue
                
                # Проверяем, есть ли рядом элементы, указывающие на отзыв
                parent = elem.parent
                if parent:
                    parent_html = str(parent).lower()
                    if any(word in parent_html for word in ['feedback', 'отзыв', 'review', 'comment']):
                        # Извлекаем данные
                        author = "Аноним"
                        rating = 0
                        date = datetime.now()
                        
                        # Ищем автора в родительском элементе
                        author_elem = parent.find(['strong', 'b', 'span'], string=re.compile(r'[А-ЯЁ][а-яё]+'))
                        if author_elem:
                            author = author_elem.get_text(strip=True)
                        
                        # Ищем рейтинг
                        rating_match = re.search(r'(\d+)\s*(звезд|star)', parent_html)
                        if rating_match:
                            rating = int(rating_match.group(1))
                        
                        reviews.append({
                            "author": author,
                            "rating": rating,
                            "text": text,
                            "date": date
                        })
            except:
                continue
        
        print(f"🔄 Альтернативным методом найдено {len(reviews)} отзывов")
        return reviews
    
    def _parse_from_html(self, soup: BeautifulSoup) -> List[Dict]:
        """Парсинг отзывов из HTML - актуальные селекторы для WB"""
        reviews = []
        
        # Актуальные селекторы для отзывов на Wildberries
        review_selectors = [
            'div.feedback__item',
            'div[class*="feedback__item"]',
            'div[data-feedback-id]',
            'article.feedback',
            'div.feedback',
            '[class*="FeedbackItem"]',
            '[class*="feedback-item"]'
        ]
        
        all_elements = []
        for selector in review_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    all_elements.extend(elements)
                    print(f"✅ Нашел {len(elements)} элементов по селектору: {selector}")
            except:
                continue
        
        # Если не нашли по селекторам, ищем по структуре
        if not all_elements:
            print("🔍 Ищу отзывы по структуре страницы...")
            # Ищем все div с текстом, похожим на отзывы
            all_divs = soup.find_all('div', class_=lambda x: x and ('feedback' in x.lower() or 'review' in x.lower() or 'comment' in x.lower()))
            all_elements.extend(all_divs)
        
        # Убираем дубликаты по тексту
        seen_texts = set()
        unique_elements = []
        for elem in all_elements:
            # Получаем текст элемента
            elem_text = elem.get_text(strip=True)
            if len(elem_text) > 20:  # Минимум 20 символов для отзыва
                text_hash = hash(elem_text[:100])  # Хеш первых 100 символов
                if text_hash not in seen_texts:
                    seen_texts.add(text_hash)
                    unique_elements.append(elem)
        
        print(f"🔍 Найдено {len(unique_elements)} уникальных элементов отзывов")
        
        for element in unique_elements:
            try:
                # Текст отзыва - ищем основной текст
                text = ""
                
                # Пробуем найти текст отзыва
                text_candidates = [
                    element.select_one('.feedback__text'),
                    element.select_one('[class*="text"]'),
                    element.select_one('[class*="content"]'),
                    element.select_one('p'),
                    element.select_one('div[class*="description"]'),
                ]
                
                for text_elem in text_candidates:
                    if text_elem:
                        text = text_elem.get_text(strip=True)
                        if len(text) > 20:
                            break
                
                # Если не нашли через селекторы, берем весь текст элемента
                if not text or len(text) < 20:
                    text = element.get_text(strip=True)
                    # Убираем лишнее (автор, дата, рейтинг)
                    lines = text.split('\n')
                    text_lines = []
                    for line in lines:
                        line = line.strip()
                        if len(line) > 10 and not any(word in line.lower() for word in ['отзыв', 'оценка', 'рейтинг', 'звезд']):
                            text_lines.append(line)
                    text = ' '.join(text_lines)
                
                if not text or len(text) < 20:
                    continue
                
                # Автор
                author = "Аноним"
                author_candidates = [
                    element.select_one('.feedback__author'),
                    element.select_one('[class*="author"]'),
                    element.select_one('[class*="user"]'),
                    element.select_one('strong'),
                    element.select_one('b'),
                    element.select_one('[class*="name"]')
                ]
                
                for author_elem in author_candidates:
                    if author_elem:
                        author_text = author_elem.get_text(strip=True)
                        if author_text and len(author_text) < 50:  # Имя не должно быть слишком длинным
                            author = author_text
                            break
                
                # Рейтинг - ищем звезды или число
                rating = 0
                
                # Ищем по классам звезд
                stars = element.select('.star, .star-filled, .active, [class*="star"]')
                if stars:
                    rating = len([s for s in stars if 'filled' in str(s.get('class', [])) or 'active' in str(s.get('class', []))])
                
                # Если не нашли звезды, ищем число
                if not rating:
                    rating_elem = element.select_one('[class*="rating"], [data-rating]')
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        rating_match = re.search(r'(\d+)', rating_text)
                        if rating_match:
                            rating = int(rating_match.group(1))
                
                # Дата
                date = datetime.now()
                date_elem = element.select_one('time, [class*="date"], [datetime]')
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    if not date_text:
                        date_text = date_elem.get('datetime', '')
                    if date_text:
                        date = self._parse_date(date_text)
                
                reviews.append({
                    "author": author,
                    "rating": rating,
                    "text": text,
                    "date": date
                })
            except Exception as e:
                print(f"⚠️ Ошибка парсинга элемента отзыва: {e}")
                continue
        
        # Убираем дубликаты по тексту
        unique_reviews = []
        seen_texts = set()
        for review in reviews:
            text_hash = hash(review["text"][:100])
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_reviews.append(review)
        
        print(f"✅ Распарсено {len(unique_reviews)} уникальных отзывов из HTML")
        return unique_reviews
    
    def _extract_reviews_via_js(self) -> List[Dict]:
        """Извлечение отзывов через JavaScript напрямую из DOM"""
        reviews = []
        try:
            # JavaScript код для извлечения отзывов
            js_code = """
            (function() {
                const reviews = [];
                
                // Ищем все возможные контейнеры отзывов
                const selectors = [
                    '.feedback__item',
                    '[class*="feedback"]',
                    '[data-feedback-id]',
                    '[id*="feedback"]',
                    'article',
                    'div[class*="review"]'
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
                        const authorElem = elem.querySelector('strong, b, [class*="author"], [class*="user"]');
                        if (authorElem) {
                            author = (authorElem.innerText || authorElem.textContent || '').trim();
                            if (author.length > 50) author = 'Аноним';
                        }
                        
                        // Ищем рейтинг
                        let rating = 0;
                        const stars = elem.querySelectorAll('[class*="star"], .star, [class*="rating"]');
                        if (stars.length > 0) {
                            rating = stars.length;
                        } else {
                            const ratingMatch = text.match(/(\\d+)\\s*(звезд|star|⭐)/i);
                            if (ratingMatch) {
                                rating = parseInt(ratingMatch[1]);
                            }
                        }
                        
                        // Ищем дату
                        let dateText = '';
                        const dateElem = elem.querySelector('time, [class*="date"]');
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
    
    def _parse_date(self, date_text: str) -> datetime:
        """Парсинг даты из текста"""
        try:
            # Различные форматы дат
            patterns = [
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 26.11.2024
                r'(\d{4})-(\d{2})-(\d{2})',  # 2024-11-26
                r'(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(\d{4})',  # 26 ноября 2024
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

