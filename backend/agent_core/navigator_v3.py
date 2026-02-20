from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse
import time


class Navigator:

    def discover(self, url):

        print(f"🧠 Navigator V3 crawling: {url}")

        product_links = []

        base_domain = urlparse(url).netloc

        MAX_CATEGORIES = 4
        MAX_PRODUCTS = 60
        CATEGORY_TIMEOUT = 12  # seconds per category

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)

            anchors = page.locator("a").all()

            category_links = []

            # ------------------------------------------------
            # STEP 1 — STRICT CATEGORY FILTER
            # ------------------------------------------------
            for a in anchors:

                try:
                    href = a.get_attribute("href") or ""
                    text = (a.inner_text() or "").lower()

                    full = urljoin(url, href)

                    parsed = urlparse(full)

                    # ✅ SAME DOMAIN ONLY
                    if parsed.netloc != base_domain:
                        continue

                    # ❌ BLOCK garbage pages
                    if any(x in full.lower() for x in [
                        "faq", "privacy", "login", "account",
                        "google.com", "youtube", "help"
                    ]):
                        continue

                    if any(x in full.lower() for x in [
                        "gift", "voucher", "category", "store"
                    ]):
                        category_links.append(full)

                except:
                    pass

            category_links = list(set(category_links))[:MAX_CATEGORIES]

            print(f"📂 Categories detected: {len(category_links)}")

            # ------------------------------------------------
            # STEP 2 — PRODUCT DISCOVERY
            # ------------------------------------------------
            for cat in category_links:

                print(f"➡️ Entering category: {cat}")

                start = time.time()

                try:
                    page.goto(cat, timeout=30000)
                    page.wait_for_timeout(2500)

                    cards = page.locator(
                        "[class*=product], [class*=card], [class*=grid]"
                    ).all()

                    for c in cards:

                        # ⏱ TIME SAFETY
                        if time.time() - start > CATEGORY_TIMEOUT:
                            print("⏱ Category timeout reached")
                            break

                        link = c.locator("a").first

                        href = link.get_attribute("href") if link else None

                        if not href:
                            continue

                        full = urljoin(cat, href)

                        parsed = urlparse(full)

                        # SAME DOMAIN ONLY
                        if parsed.netloc != base_domain:
                            continue

                        if any(x in full.lower() for x in [
                            "product", "voucher", "gift"
                        ]):
                            product_links.append(full)

                        # 🧠 LIMIT PRODUCTS
                        if len(product_links) >= MAX_PRODUCTS:
                            break

                except Exception as e:
                    print(f"⚠️ Category error: {e}")

            browser.close()

        product_links = list(set(product_links))

        print(f"✅ Navigator V3 found {len(product_links)} REAL product links")

        return {
            "url": url,
            "product_links": product_links
        }
