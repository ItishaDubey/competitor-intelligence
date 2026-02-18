import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def scrape_url_smart(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
        page = await context.new_page()
        try:
            print(f"🕵️ Agent Deep-Scanning: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            products = await page.evaluate('''() => {
                const noise = ["login", "home", "cart", "account", "help", "sign in"];
                const items = [];
                const cards = document.querySelectorAll('div[class*="product"], div[class*="item"], article, .card');
                cards.forEach(el => {
                    const name = el.querySelector('h2, h3, h4, [class*="title"], [class*="name"]')?.innerText.trim();
                    const priceEl = Array.from(el.querySelectorAll('span, div, p, b')).find(n => n.innerText.match(/[\\$₹€]/));
                    const price = priceEl?.innerText.trim();
                    if (name && price && !noise.some(n => name.toLowerCase().includes(n))) {
                        items.push({ name, price, raw_price: parseFloat(price.replace(/[^0-9.]/g, '')) || 0 });
                    }
                });
                return items;
            }''')
            return {"url": url, "products": products, "product_count": len(products)}
        except Exception as e:
            return {"url": url, "products": [], "error": str(e)}
        finally:
            await browser.close()