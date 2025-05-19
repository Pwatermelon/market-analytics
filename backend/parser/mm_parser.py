import asyncio
from playwright.async_api import async_playwright

async def search_mm_products(query: str):
    print(f"=== MM SEARCH START: {query} ===")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="ru-RU"
            )
            page = await context.new_page()
            url = f"https://mm.ru/search?query={query}"
            print(f"[MM] URL: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('div.ui-card', timeout=20000)
            products = []
            cards = await page.query_selector_all('div.ui-card')
            print(f"[MM] Найдено карточек: {len(cards)}")
            for card in cards[:10]:
                try:
                    # Название
                    title_el = await card.query_selector('.card-info-block')
                    title = await title_el.inner_text() if title_el else ''
                    # Ссылка
                    link_el = await card.query_selector('a')
                    link = await link_el.get_attribute('href') if link_el else None
                    if link and not link.startswith('http'):
                        link = f'https://mm.ru{link}'
                    # Картинка
                    img_el = await card.query_selector('img')
                    img = await img_el.get_attribute('src') if img_el else None
                    # Цена
                    price_el = await card.query_selector('.price')
                    price = await price_el.inner_text() if price_el else ''
                    # product_id из ссылки
                    import re
                    m = re.search(r'/product/([\w-]+)-(\d+)', link or '')
                    product_id = m.group(2) if m else link
                    products.append({
                        'title': title.strip(),
                        'price': price.strip(),
                        'img': img,
                        'link': link,
                        'product_id': product_id,
                        'source': 'mm',
                    })
                except Exception as e:
                    print(f"[MM] Ошибка карточки: {e}")
                    continue
            await browser.close()
            print(f"=== MM SEARCH END: найдено товаров {len(products)} ===")
            return {'products': products}
    except Exception as e:
        print(f'=== MM SEARCH ERROR: {e} ===')
        import traceback; traceback.print_exc()
        return {'products': []}

async def get_all_reviews_mm(product_id: str, max_pages: int = 3):
    print(f"=== MM REVIEWS START: {product_id} ===")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            url = f"https://mm.ru/product/{product_id}"
            print(f"[MM] URL: {url}")
            await page.goto(url, timeout=60000)
            # Кликаем по вкладке "Отзывы" мышкой
            tabs = await page.query_selector_all('div.product-tab')
            clicked = False
            for tab in tabs:
                tab_text = await tab.inner_text()
                if 'Отзывы' in tab_text:
                    box = await tab.bounding_box()
                    if box:
                        await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                        await page.mouse.down()
                        await page.mouse.up()
                        print('[MM] mouse клик по вкладке "Отзывы"')
                        clicked = True
                    else:
                        print('[MM] bounding_box не найден для вкладки "Отзывы"')
                    break
            if not clicked:
                print('[MM] Вкладка "Отзывы" не найдена!')
            # Ждём появления блока .reviews
            await page.wait_for_selector('.reviews', timeout=10000)
            # Прокручиваем к блоку .reviews
            reviews_block = await page.query_selector('.reviews')
            if reviews_block:
                await reviews_block.scroll_into_view_if_needed()
            else:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
            # Ждём появления отзывов с увеличенным таймаутом
            await page.wait_for_selector('.feedback-item', timeout=10000)
            reviews = []
            items = await page.query_selector_all('.feedback-item')
            print(f"[MM] Найдено отзывов: {len(items)}")
            for item in items:
                try:
                    text_el = await item.query_selector('div.content')
                    text = await text_el.inner_text() if text_el else ''
                    stars_el = await item.query_selector('div.top-heading-stars')
                    stars = 0
                    if stars_el:
                        stars_svgs = await stars_el.query_selector_all('svg')
                        stars = len(stars_svgs)
                    reviews.append({'text': text.strip(), 'stars': stars})
                except Exception as e:
                    print(f"[MM] Ошибка отзыва: {e}")
                    continue
            await browser.close()
            print(f"=== MM REVIEWS END: найдено отзывов {len(reviews)} ===")
            return reviews
    except Exception as e:
        print(f'=== MM REVIEWS ERROR: {e} ===')
        import traceback; traceback.print_exc()
        return [] 