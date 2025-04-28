import asyncio
import random
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, Response
from fake_useragent import UserAgent

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

# Список прокси-серверов (примеры, нужно заменить на реальные)
# Временно отключаем использование прокси
PROXIES = []

class BrowserManager:
    _instance = None
    _browser = None
    _playwright = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Инициализация браузера"""
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
    
    async def get_page(self, proxy: Optional[str] = None) -> Page:
        """Получение новой страницы с настройками"""
        if self._browser is None:
            await self.initialize()
        
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
    
    async def get_random_proxy(self) -> Optional[str]:
        """Получение случайного прокси"""
        return random.choice(PROXIES) if PROXIES else None
    
    async def search_products(self, url: str, marketplace: str, query: str) -> Dict[str, Any]:
        """Поиск товаров на маркетплейсе"""
        page = await self.get_page()
        try:
            logger.info(f"Searching for '{query}' on {marketplace}")
            
            # Переходим на страницу поиска
            await page.goto(url, wait_until="networkidle")
            
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
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(r => setTimeout(r, 1000));
                window.scrollTo(0, 0);
            """)
            
            # Получаем HTML страницы
            html = await page.content()
            
            # Закрываем страницу
            await page.close()
            
            return {
                "html": html,
                "status": "success",
                "marketplace": marketplace,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Error searching products on {marketplace}: {str(e)}", exc_info=True)
            await page.close()
            return {
                "html": "",
                "status": "error",
                "marketplace": marketplace,
                "query": query,
                "error": str(e)
            } 