"""
Targeted diagnostic - gets full Woohoo product object + Flipkart JSON-LD
Run: python3 diagnose2.py > diagnose2_output.txt 2>&1
"""
import json, re
from playwright.sync_api import sync_playwright

WOOHOO_URL   = "https://www.woohoo.in/brand-gift-cards"
FLIPKART_URL = "https://www.flipkart.com/search?q=gift+card&otracker=search"

def run(url, label):
    print(f"\n{'='*60}\nDIAGNOSING: {label}\n{'='*60}")
    all_products = []
    pages_seen = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            viewport={"width":1440,"height":900}, locale="en-IN", timezone_id="Asia/Kolkata"
        )
        page = ctx.new_page()

        def on_response(response):
            try:
                if "woohoo.in/proxy/category" in response.url:
                    page_num = response.url.split("page=")[-1] if "page=" in response.url else "?"
                    if page_num in pages_seen:
                        return
                    pages_seen.add(page_num)
                    data = response.json()
                    products = data.get("data", {}).get("_embedded", {}).get("products", [])
                    print(f"\n  PAGE {page_num}: {len(products)} products")
                    if products:
                        # Print FULL first product so we can see all fields
                        print(f"  FULL product[0]:\n{json.dumps(products[0], indent=2)[:3000]}")
                        all_products.extend(products)
                elif "flipkart" in response.url and "json" in response.headers.get("content-type",""):
                    data = response.json()
                    txt = json.dumps(data)
                    if "price" in txt.lower() and len(txt) > 500:
                        print(f"\n  FK XHR [{len(txt)}]: {response.url[:80]}")
                        print(f"  {txt[:400]}")
            except: pass

        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        for _ in range(12):
            page.evaluate("window.scrollBy(0, window.innerHeight*2)")
            page.wait_for_timeout(500)
        page.wait_for_timeout(2000)

        if "woohoo" in url:
            # Read __INITIAL_STATE__ which has page 1
            state = page.evaluate("""
                () => {
                    try {
                        return JSON.stringify(window.__INITIAL_STATE__);
                    } catch(e) { return null; }
                }
            """)
            if state:
                data = json.loads(state)
                # Traverse to find products
                def find_products(obj, path="", depth=0):
                    if depth > 8: return
                    if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
                        if "entity_id" in obj[0] or "sku" in obj[0] or "name" in obj[0]:
                            print(f"\n  __INITIAL_STATE__ products at {path} ({len(obj)} items)")
                            print(f"  FULL item[0]:\n{json.dumps(obj[0], indent=2)[:2000]}")
                            all_products.extend(obj)
                            return
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            find_products(v, f"{path}.{k}", depth+1)
                    elif isinstance(obj, list):
                        for i, v in enumerate(obj[:3]):
                            find_products(v, f"{path}[{i}]", depth+1)
                find_products(data)

        if "flipkart" in url:
            # Read JSON-LD schema
            scripts = page.evaluate("""
                () => Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                          .map(s => s.textContent)
            """)
            for s in scripts:
                try:
                    data = json.loads(s)
                    print(f"\n  JSON-LD type={data.get('@type')}")
                    print(f"  FULL:\n{json.dumps(data, indent=2)[:3000]}")
                except: pass

            # Also try reading the page HTML for embedded product data
            html = page.content()
            # Flipkart sometimes embeds product data in a script as JSON
            matches = re.findall(r'"title"\s*:\s*"([^"]{5,80}gift[^"]{0,40})"', html, re.IGNORECASE)
            print(f"\n  Product titles found in HTML: {matches[:20]}")
            
            # Find any price data
            price_matches = re.findall(r'"finalPrice"\s*:\s*(\{[^}]+\})', html)
            print(f"\n  finalPrice matches: {price_matches[:5]}")
            
            price_matches2 = re.findall(r'"price"\s*:\s*"?([\d,]+)"?', html)
            print(f"  price field values (first 20): {price_matches2[:20]}")

        browser.close()

    print(f"\n  Total products collected: {len(all_products)}")
    if all_products:
        # Show unique name field candidates
        sample = all_products[0]
        print(f"\n  All fields in product[0]: {list(sample.keys())}")
        # Find name-like fields
        for k, v in sample.items():
            if isinstance(v, str) and 3 < len(v) < 100:
                print(f"    {k}: {v!r}")

run(WOOHOO_URL, "Woohoo")
run(FLIPKART_URL, "Flipkart")
print("\nDone.")