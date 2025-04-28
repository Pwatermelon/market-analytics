import asyncio
import random
import logging
import aiohttp
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, Response
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Список User-Agent для ротации
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

class ProxyManager:
    def __init__(self):
        self.proxies: List[str] = []
        self.current_index = 0
        
    async def load_proxies(self, proxy_url: Optional[str] = None):
        """Загрузка списка прокси из файла или API"""
        if proxy_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(proxy_url) as response:
                        proxies_data = await response.json()
                        # Предполагаем, что API возвращает список прокси в формате:
                        # [{"ip": "...", "port": "...", "username": "...", "password": "..."}]
                        self.proxies = [
                            f"http://{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
                            for proxy in proxies_data
                        ]
            except Exception as e:
                logger.error(f"Failed to load proxies from API: {e}")
        
        # Если не удалось загрузить прокси или URL не предоставлен,
        # используем резервный список (замените на ваши реальные прокси)
        if not self.proxies:
            self.proxies = [
                "http://proxy1.example.com:8080",
                "http://proxy2.example.com:8080",
                # Добавьте ваши прокси здесь
            ]
    
    def get_next_proxy(self) -> Optional[str]:
        """Получение следующего прокси из списка"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

class BrowserManager:
    _instance = None
    _browser = None
    _playwright = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
            cls._instance.proxy_manager = ProxyManager()
        return cls._instance
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def initialize(self):
        """Инициализация браузера с повторными попытками"""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-infobars',
                    '--window-size=1920,1080',
                ]
            )
            logger.info("Browser initialized")
    
    async def close(self):
        """Закрытие браузера"""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser closed")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_page(self, proxy: Optional[str] = None) -> Page:
        """Получение новой страницы с настройками и механизмом повторных попыток"""
        if self._browser is None:
            await self.initialize()
        
        # Если прокси не указан явно, получаем следующий из менеджера
        if not proxy:
            proxy = await self.proxy_manager.get_next_proxy()
        
        # Генерируем случайный User-Agent
        ua = UserAgent()
        user_agent = ua.random
        
        # Настройки контекста
        context_options = {
            "user_agent": user_agent,
            "viewport": {"width": 1920, "height": 1080},
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "has_touch": True,
            "is_mobile": False,
            "locale": "ru-RU",
            "timezone_id": "Europe/Moscow",
            "geolocation": {"latitude": 55.7558, "longitude": 37.6173},
            "permissions": ["geolocation"],
        }
        
        # Добавляем прокси, если указан
        if proxy:
            context_options["proxy"] = {
                "server": proxy,
                "username": "user",  # Заменить на реальные данные
                "password": "pass",  # Заменить на реальные данные
            }
        
        # Создаем контекст и страницу
        context = await self._browser.new_context(**context_options)
        
        # Добавляем скрипты для обхода обнаружения автоматизации
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ru-RU', 'ru', 'en-US', 'en']
            });
            window.chrome = {
                runtime: {}
            };
        """)
        
        page = await context.new_page()
        
        # Устанавливаем обработчики событий
        await page.route("**/*", self._handle_route)
        
        # Добавляем случайную задержку
        await asyncio.sleep(random.uniform(1, 3))
        
        return page
    
    async def _handle_route(self, route):
        """Обработчик маршрутов для блокировки ненужных ресурсов"""
        # Разрешаем загрузку изображений
        if route.request.resource_type in ["image"]:
            await route.continue_()
        # Блокируем ненужные ресурсы
        elif route.request.resource_type in ["font", "media", "other"]:
            await route.abort()
        else:
            await route.continue_()
    
    async def handle_captcha(self, page: Page) -> bool:
        """Обработка капчи (заготовка для реализации)"""
        try:
            # Проверяем наличие капчи по известным селекторам
            captcha_selectors = [
                "iframe[src*='captcha']",
                ".captcha",
                "#captcha",
                "[data-testid='captcha']"
            ]
            
            for selector in captcha_selectors:
                if await page.locator(selector).count() > 0:
                    logger.warning("Captcha detected!")
                    # Здесь можно добавить логику решения капчи
                    # Например, использование сервисов типа 2captcha или рукапча
                    return True
            return False
        except Exception as e:
            logger.error(f"Error handling captcha: {e}")
            return False
    
    async def search_products(self, url: str, marketplace: str, query: str) -> Dict[str, Any]:
        """Улучшенный метод поиска товаров с обработкой ошибок"""
        page = None
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                if page:
                    await page.close()
                
                page = await self.get_page()
                logger.info(f"Searching for '{query}' on {marketplace}")
                
                # Переходим на страницу поиска
                response = await page.goto(url, wait_until="networkidle")
                
                if not response.ok:
                    raise Exception(f"Failed to load page: {response.status}")
                
                # Проверяем наличие капчи
                if await self.handle_captcha(page):
                    retry_count += 1
                    continue
                
                # Добавляем случайную задержку для имитации человеческого поведения
                await asyncio.sleep(random.uniform(2, 4))
                
                # Выбираем селектор ожидания в зависимости от маркетплейса
                if marketplace == "ozon":
                    selector = '[data-widget="searchResultsV2"] [data-index], [data-index]'
                elif marketplace == "wildberries":
                    selector = '.product-card, .catalog-item, .product-card__main, [data-product-id], .product-card__container, .catalog-item__container'
                elif marketplace == "yandexmarket":
                    selector = 'div[data-zone-name="snippet"]'
                else:
                    selector = ".product-card, .catalog-item"
                
                # Ждем загрузки результатов
                await page.wait_for_selector(selector, timeout=30000)
                
                # Прокручиваем страницу для загрузки всех изображений
                await page.evaluate("""
                    async function autoScroll() {
                        await new Promise((resolve) => {
                            let totalHeight = 0;
                            const distance = 100;
                            const timer = setInterval(() => {
                                const scrollHeight = document.body.scrollHeight;
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                
                                if(totalHeight >= scrollHeight){
                                    clearInterval(timer);
                                    window.scrollTo(0, 0);
                                    resolve();
                                }
                            }, 100);
                        });
                    }
                    return autoScroll();
                """)
                
                # Ждем завершения прокрутки
                await asyncio.sleep(1.5)
                
                # Получаем HTML страницы
                html = await page.content()
                
                return {
                    "html": html,
                    "status": "success",
                    "marketplace": marketplace,
                    "query": query
                }
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Attempt {retry_count}/{max_retries} failed: {str(e)}", exc_info=True)
                await asyncio.sleep(random.uniform(2, 5))
                
            finally:
                if page:
                    await page.close()
        
        return {
            "html": "",
            "status": "error",
            "marketplace": marketplace,
            "query": query,
            "error": f"Failed after {max_retries} attempts"
        } 