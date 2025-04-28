import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки прокси
PROXY_API_URL = os.getenv('PROXY_API_URL', '')
PROXY_API_KEY = os.getenv('PROXY_API_KEY', '')

# Настройки антикапчи
ANTICAPTCHA_KEY = os.getenv('ANTICAPTCHA_KEY', '')
TWOCAPTCHA_KEY = os.getenv('TWOCAPTCHA_KEY', '')

# Настройки браузера
BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-gpu',
    '--disable-infobars',
    '--window-size=1920,1080',
]

# Таймауты и задержки
REQUEST_TIMEOUT = 30  # секунд
RETRY_DELAY = 5  # секунд
MAX_RETRIES = 3

# Настройки парсинга
MAX_PRODUCTS_PER_SEARCH = 100
MAX_PRODUCTS_FOR_DETAILS = 10

# Пути для сохранения результатов
RESULTS_DIR = 'results'
os.makedirs(RESULTS_DIR, exist_ok=True)

# Настройки логирования
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# Настройки User-Agent
ROTATE_USER_AGENT = True
USER_AGENT_UPDATE_INTERVAL = 3600  # секунд

# Настройки для каждого маркетплейса
MARKETPLACE_CONFIG = {
    'ozon': {
        'base_url': 'https://www.ozon.ru',
        'search_url': 'https://www.ozon.ru/search/',
        'product_selector': '[data-widget="searchResultsV2"]',
        'max_pages': 5,
    },
    'wildberries': {
        'base_url': 'https://www.wildberries.ru',
        'search_url': 'https://www.wildberries.ru/catalog/0/search.aspx',
        'product_selector': '.product-card',
        'max_pages': 5,
    },
    'yandexmarket': {
        'base_url': 'https://market.yandex.ru',
        'search_url': 'https://market.yandex.ru/search',
        'product_selector': 'div[data-zone-name="snippet"]',
        'max_pages': 5,
    }
} 