from typing import Dict, List
from playwright.async_api import async_playwright
import asyncio
import re

# Получение product_id из ссылки на товар
PRODUCT_ID_RE = re.compile(r'/catalog/(\d+)/')

async def get_all_reviews(product_id: str, max_reviews: int = 50) -> List[dict]:
    feedbacks_url = f'https://www.wildberries.ru/catalog/{product_id}/feedbacks'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        await page.goto(feedbacks_url)
        try:
            await page.wait_for_selector('.comments__item', timeout=15000)
        except Exception:
            print(f'Отзывы не найдены на {feedbacks_url}')
            await browser.close()
            return []
        # Прокручиваем вниз, чтобы подгрузить все отзывы
        last_height = 0
        for _ in range(20):  # максимум 20 прокруток
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1200)
            new_height = await page.evaluate('document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height
        reviews = []
        items = await page.query_selector_all('.comments__item')
        for item in items[:max_reviews]:
            text = await item.inner_text()
            # Оценка (звёзды)
            stars = 0
            rating_el = await item.query_selector('.feedback__rating')
            if rating_el:
                rating_class = await rating_el.get_attribute('class')
                m = re.search(r'star(\d)', rating_class or '')
                if m:
                    stars = int(m.group(1))
            reviews.append({'text': text.strip(), 'stars': stars})
        await browser.close()
        return reviews

async def search_wb_products(query: str) -> Dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
        await page.goto(url)
        html = await page.content()
        print('=== WB PAGE HTML START ===')
        print(html[:2000])  # Логируем первые 2000 символов для диагностики
        print('=== WB PAGE HTML END ===')
        await page.wait_for_selector('.product-card__wrapper', timeout=20000)
        products = []
        cards = await page.query_selector_all('.product-card__wrapper')
        for card in cards[:10]:  # первые 10 товаров
            title_el = await card.query_selector('.product-card__name')
            price_el = await card.query_selector('.price__lower-price')
            img_el = await card.query_selector('img')
            link_el = await card.query_selector('a.product-card__link')
            link = await link_el.get_attribute('href') if link_el else None
            if not (title_el and price_el and img_el and link):
                continue
            title = (await title_el.inner_text()).strip()
            price = (await price_el.inner_text()).strip()
            img = await img_el.get_attribute('src')
            product_url = link
            if product_url.startswith('/'):
                product_url = f'https://www.wildberries.ru{link}'
            m = PRODUCT_ID_RE.search(product_url)
            if not m:
                continue
            product_id = m.group(1)
            products.append({
                "title": title,
                "price": price,
                "img": img,
                "link": product_url,
                "product_id": product_id,
                "source": "wb"
            })
        await browser.close()
        return {"products": products} 