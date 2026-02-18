import asyncio
import json
import logging
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import html2text

# --- ROBUST STEALTH IMPORT ---
try:
    from playwright_stealth import stealth_async
except ImportError:
    try:
        from playwright_stealth.stealth import stealth_async
    except ImportError:
        async def stealth_async(page): pass

# Initialize Server
mcp = FastMCP("UniversalBrowser")

async def get_page_content_safe(url, retries=3):
    """
    Universal Stealth Fetcher.
    Mimics a real human user on a Mac to bypass anti-bots on ANY site.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ]
        )
        
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            device_scale_factor=2,
            locale="en-US",
            timezone_id="Asia/Kolkata"
        )
        
        page = await context.new_page()
        await stealth_async(page)

        for attempt in range(retries):
            try:
                print(f"Attempt {attempt+1}: Navigating to {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000) # Human pause
                
                # Scroll down to trigger lazy-loading images/prices
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await page.wait_for_timeout(1000)

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

def extract_universal_data(soup):
    """
    Extracts structured data (JSON-LD) and Meta tags common to ALL e-commerce sites.
    """
    data = {"structured": [], "meta": {}}

    # 1. JSON-LD (The Gold Standard for E-commerce)
    # Most sites (Shopify, Walmart, etc.) put product data here.
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            json_content = json.loads(script.string)
            data["structured"].append(json_content)
        except:
            continue

    # 2. OpenGraph / Meta Tags (The Silver Standard)
    # Works on almost any site with social sharing
    metas = {
        "og:title": "title",
        "og:price:amount": "price",
        "product:price:amount": "price",
        "og:description": "description",
        "twitter:data1": "price" 
    }
    for tag, key in metas.items():
        element = soup.find("meta", property=tag) or soup.find("meta", attrs={"name": tag})
        if element and element.get("content"):
            data["meta"][key] = element["content"]

    return data

@mcp.tool()
async def scrape_product(url: str) -> str:
    """
    Universally scrapes ANY e-commerce URL.
    Returns a mix of Structured Data (JSON-LD) and Visual Text (Markdown).
    """
    try:
        raw_html = await get_page_content_safe(url)
        if not raw_html:
            return "Error: Failed to load page."

        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # A. Get Hidden Structured Data
        universal_data = extract_universal_data(soup)
        
        # B. Get Visual Text (Markdown)
        converter = html2text.HTML2Text()
        converter.ignore_links = True
        converter.ignore_images = True
        converter.body_width = 0 # No wrapping
        markdown = converter.handle(str(soup))
        
        # C. Construct the "Bulletproof Context" for the Agent
        # We give the Agent EVERYTHING we found, so IT decides what's relevant.
        report = f"""
--- SOURCE URL: {url} ---

=== 1. DETECTED METADATA (High Confidence) ===
{json.dumps(universal_data, indent=2)}

=== 2. VISUAL PAGE CONTENT (Markdown) ===
{markdown[:4000]} 
... (content truncated for brevity)
"""
        return report

    except Exception as e:
        return f"Scraping Error: {str(e)}"

if __name__ == "__main__":
    try:
        mcp.run()
    except KeyboardInterrupt:
        pass