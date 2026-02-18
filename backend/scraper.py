# backend/scraper.py
import asyncio
import json
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import html2text

# Try to import stealth, define dummy if missing
try:
    from playwright_stealth import stealth_async
except ImportError:
    async def stealth_async(page): pass

async def scrape_url_smart(url: str):
    """
    Bulletproof Scraper: Handles Amazon, Rooter, and generic sites.
    Returns: { "price": float, "title": str, "product_count": int, "raw_text": str }
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        await stealth_async(page)
        
        try:
            print(f"🕵️ Scanning: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000) # Human pause
            
            # Scroll to trigger lazy loads
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
            await page.wait_for_timeout(1000)

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # --- EXTRACTION LOGIC ---
            data = {"price": None, "title": None, "product_count": 0, "raw_text": ""}
            
            # 1. Title
            data['title'] = soup.title.string if soup.title else "Unknown Page"
            
            # 2. Universal Price Extraction (Regex)
            text = soup.get_text()
            # Look for prices like $10.99, ₹500, etc.
            prices = re.findall(r'[\$₹€]\s?(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
            valid_prices = []
            for p in prices:
                try:
                    val = float(p.replace(',', ''))
                    if 1 < val < 10000: valid_prices.append(val)
                except: continue
            
            if valid_prices:
                # Heuristic: The most common price or the first reasonable one is often the product price
                data['price'] = valid_prices[0]
            
            # 3. Product Count (Heuristic: Count 'Add to Cart' buttons or similar)
            product_elements = soup.select('.product, .item, [data-component-type="s-search-result"], .card')
            data['product_count'] = len(product_elements) if len(product_elements) > 0 else 1
            
            # 4. JSON-LD fallback (High Accuracy)
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    jd = json.loads(script.string)
                    if isinstance(jd, list): jd = jd[0]
                    if jd.get('@type') == 'Product':
                        data['title'] = jd.get('name', data['title'])
                        offers = jd.get('offers', {})
                        if isinstance(offers, list) and offers: offers = offers[0]
                        data['price'] = float(offers.get('price', data['price'] or 0))
                except: continue

            return data

        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return {"error": str(e)}
        finally:
            await browser.close()