import asyncio
import json
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from bs4 import BeautifulSoup
import html2text

# Initialize the MCP Server
mcp = FastMCP("BulletproofBrowser")

async def get_page_content_safe(url, retries=3):
    """
    Launches a stealth browser to fetch the page content.
    Retries on failure (common with Amazon/proxies).
    """
    async with async_playwright() as p:
        # Launch browser with anti-detection args
        browser = await p.chromium.launch(
            headless=True,  # Set to False if you want to see the browser open
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        # Create a context that looks like a real MacBook user
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            device_scale_factor=2,
        )
        
        page = await context.new_page()
        
        # ACTIVATE STEALTH MODE
        await stealth_async(page)

        for attempt in range(retries):
            try:
                print(f"Attempt {attempt+1}: Navigating to {url}")
                # Wait up to 30 seconds for the page to load
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Random wait to mimic human behavior
                await page.wait_for_timeout(2000)
                
                # Special wait for Amazon price to load
                if "amazon" in url:
                    try:
                        await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=5000)
                    except:
                        pass # Continue even if selector isn't found immediately

                content = await page.content()
                await browser.close()
                return content
                
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                if attempt == retries - 1:
                    await browser.close()
                    raise e
                await asyncio.sleep(2)
        
        await browser.close()
        return None

@mcp.tool()
async def scrape_product(url: str) -> str:
    """
    Scrapes a product page. Automatically handles Amazon, Rooter, and generic sites.
    Returns a JSON string or Markdown text.
    """
    try:
        raw_html = await get_page_content_safe(url)
        if not raw_html:
            return "Error: Failed to load page after retries."

        soup = BeautifulSoup(raw_html, 'html.parser')

        # --- STRATEGY 1: Rooter (JSON Intercept) ---
        if "rooter.gg" in url:
            script = soup.find('script', id='__NEXT_DATA__')
            if script:
                try:
                    data = json.loads(script.string)
                    # Navigate to the product data in the JSON
                    props = data.get('props', {}).get('pageProps', {})
                    product = props.get('product') or props.get('initialState', {}).get('shop', {})
                    
                    return json.dumps({
                        "site": "Rooter",
                        "title": product.get('name', 'Unknown'),
                        "price": product.get('price', 'Unknown'),
                        "currency": product.get('currency', 'INR'),
                        "status": "Available"  # Rooter usually doesn't show OOS in this JSON
                    }, indent=2)
                except Exception as e:
                    return f"Rooter JSON found but parsing failed: {e}"

        # --- STRATEGY 2: Amazon (Visual Selectors) ---
        if "amazon" in url:
            products = []
            # Find all search result cards
            results = soup.select('[data-component-type="s-search-result"]')
            
            for item in results[:5]: # Get top 5
                title_el = item.select_one("h2 a span")
                price_whole = item.select_one(".a-price-whole")
                
                if title_el:
                    products.append({
                        "title": title_el.get_text().strip(),
                        "price": price_whole.get_text().strip() if price_whole else "N/A",
                        "link": "https://amazon.in" + item.select_one("h2 a")['href']
                    })
            
            if products:
                return json.dumps({"site": "Amazon", "products": products}, indent=2)
            else:
                return "Amazon page loaded, but no products found. Captcha might have triggered."

        # --- STRATEGY 3: Generic (Markdown Fallback) ---
        # For 99gifts and others
        converter = html2text.HTML2Text()
        converter.ignore_links = True
        converter.ignore_images = True
        markdown = converter.handle(str(soup))
        
        # Return the first 3000 chars of text for the LLM to read
        return f"GENERIC SITE CONTENT (Parse this):\n\n{markdown[:3000]}"

    except Exception as e:
        return f"Fatal Error scraping {url}: {str(e)}"

if __name__ == "__main__":
    mcp.run()