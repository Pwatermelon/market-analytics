import asyncio
from playwright.async_api import async_playwright

# Поиск товаров на Яндекс.Маркете
async def search_ym_products(query: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ru-RU",
            extra_http_headers={
                "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        )
        page = await context.new_page()
        url = f"https://market.yandex.ru/search?text={query}"
        await page.goto(url, timeout=60000)
        try:
            await page.wait_for_selector('[data-zone-name="snippet-card"]', timeout=60000)
        except Exception as e:
            html = await page.content()
            print("=== YM PAGE HTML START ===")
            print(html[:2000])
            print("=== YM PAGE HTML END ===")
            if any(word in html.lower() for word in ["captcha", "stub", "вы робот", "ошибка", "403", "404"]):
                print("[YM PARSER] Похоже, страница заблокирована или выдана капча/stub/ошибка!")
            await browser.close()
            raise e
        products = []
        items = await page.query_selector_all('[data-zone-name="snippet-card"]')
        for item in items[:10]:
            try:
                title = await item.query_selector_eval('[data-zone-name="title"]', 'el => el.textContent')
                price = await item.query_selector_eval('[data-auto="mainPrice"]', 'el => el.textContent')
                img = await item.query_selector_eval('img', 'el => el.src')
                link = await item.query_selector_eval('a[data-zone-name="title"]', 'el => el.href')
                # product_id теперь из ссылки вида /card/имя/ID
                import re
                m = re.search(r'/card/[^/]+/(\d+)', link)
                product_id = m.group(1) if m else link
                products.append({
                    'title': title.strip() if title else '',
                    'price': price.strip() if price else '',
                    'img': img,
                    'link': link,
                    'product_id': product_id,
                    'source': 'ym',
                })
            except Exception as e:
                continue
        await browser.close()
        return {'products': products}

# Получение всех отзывов по product_id
async def get_all_reviews_ym(product_id: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = f"https://market.yandex.ru/product--/{product_id}/reviews"
        await page.goto(url, timeout=60000)
        await page.wait_for_selector('[data-auto="review"]', timeout=60000)
        reviews = []
        # Прокручиваем и кликаем "Показать ещё", если есть
        while True:
            review_items = await page.query_selector_all('[data-auto="review"]')
            for item in review_items[len(reviews):]:
                try:
                    text = await item.query_selector_eval('[data-auto="review-text"]', 'el => el.textContent')
                    stars = await item.query_selector_eval('[data-auto="rating-badge-value"]', 'el => parseInt(el.textContent)')
                    reviews.append({'text': text.strip() if text else '', 'stars': stars or 0})
                except Exception:
                    continue
            # Кнопка "Показать ещё"
            try:
                more_btn = await page.query_selector('[data-auto="pager-more"]')
                if more_btn:
                    await more_btn.click()
                    await page.wait_for_timeout(1500)
                else:
                    break
            except Exception:
                break
        await browser.close()
        return reviews 