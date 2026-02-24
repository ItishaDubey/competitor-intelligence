"""
Diagnostic script - runs in your environment to show exactly what
Woohoo and Flipkart return so we can build accurate parsers.
Run: python3 /tmp/diagnose.py
"""
import json, re, sys
from urllib.parse import urlparse, urljoin
from playwright.sync_api import sync_playwright

WOOHOO_URL  = "https://www.woohoo.in/brand-gift-cards"
FLIPKART_URL = "https://www.flipkart.com/search?q=gift+card&otracker=search"

def diagnose(url, label):
    print(f"\n{'='*60}")
    print(f"DIAGNOSING: {label}")
    print(f"{'='*60}")
    
    api_calls = []
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage",
                  "--disable-blink-features=AutomationControlled"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            viewport={"width":1440,"height":900},
            locale="en-IN", timezone_id="Asia/Kolkata"
        )
        page = ctx.new_page()
        
        def on_response(response):
            try:
                ct = response.headers.get("content-type","")
                if "json" not in ct: return
                data = response.json()
                txt = json.dumps(data)
                api_calls.append({
                    "url": response.url,
                    "size": len(txt),
                    "snippet": txt[:300],
                    "data": data
                })
            except: pass
        
        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)
        
        # Scroll to trigger lazy loads
        for _ in range(8):
            page.evaluate("window.scrollBy(0, window.innerHeight*2)")
            page.wait_for_timeout(700)
        
        # Get all script tag contents
        scripts = page.evaluate("""
            () => Array.from(document.querySelectorAll('script'))
                      .map(s=>({src: s.src||'inline', text: (s.textContent||'').substring(0,500)}))
                      .filter(s=>s.text.length > 50)
        """)
        
        # Get page HTML snippet
        html_snippet = page.content()[:2000]
        
        browser.close()
    
    print(f"\n📡 API calls captured: {len(api_calls)}")
    for c in api_calls[:20]:
        print(f"  [{c['size']:6} chars] {c['url'][:100]}")
        print(f"           {c['snippet'][:120]}")
    
    print(f"\n📜 Script tags: {len(scripts)}")
    for s in scripts[:10]:
        print(f"  src={s['src'][:60]}")
        if 'inline' in s['src']:
            print(f"  text={s['text'][:150]}")
    
    print(f"\n🌐 HTML snippet:")
    print(html_snippet[:1000])
    
    # Try to find product-like data in API calls
    print(f"\n🔍 Looking for product data in API responses...")
    for c in api_calls:
        d = c["data"]
        txt = json.dumps(d).lower()
        if any(k in txt for k in ["gift","voucher","brand","product"]):
            print(f"\n  ✅ PROMISING: {c['url'][:80]}")
            # Try to find arrays
            def find_arrays(obj, path="", depth=0):
                if depth > 5: return
                if isinstance(obj, list) and len(obj) > 2:
                    sample = obj[0] if obj else {}
                    if isinstance(sample, dict):
                        keys = list(sample.keys())[:8]
                        print(f"    Array at {path}: {len(obj)} items, keys={keys}")
                        if obj:
                            print(f"    Sample: {json.dumps(obj[0])[:200]}")
                elif isinstance(obj, dict):
                    for k,v in obj.items():
                        find_arrays(v, f"{path}.{k}", depth+1)
            find_arrays(d)
    
    return api_calls

if __name__ == "__main__":
    diagnose(WOOHOO_URL, "Woohoo")
    diagnose(FLIPKART_URL, "Flipkart")
    print("\nDone.")