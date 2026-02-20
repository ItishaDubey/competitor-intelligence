from playwright.sync_api import sync_playwright
from urllib.parse import urljoin


class Navigator:

    def discover(self, url):

        print(f"🧠 Navigator V3 crawling: {url}")

        product_links = []

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            )

            page = context.new_page()

            # ------------------------------
            # STEP 0 — OPEN PAGE SAFELY
            # ------------------------------
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2500)

            # ------------------------------
            # STEP 1 — FIND CATEGORY LINKS
            # ------------------------------
            anchors = page.locator("a")

            category_links = []

            anchor_count = min(anchors.count(), 150)

            for i in range(anchor_count):

                try:
                    a = anchors.nth(i)

                    href = a.get_attribute("href") or ""
                    text = (a.inner_text() or "").lower()

                    # ❌ Ignore garbage navigation
                    if any(x in text for x in [
                        "login", "account", "cart", "privacy",
                        "terms", "footer", "contact", "help"
                    ]):
                        continue

                    # ✅ Category patterns
                    if any(x in href.lower() for x in [
                        "gift", "voucher", "category", "store"
                    ]):
                        category_links.append(urljoin(url, href))

                except:
                    continue

            category_links = list(set(category_links))[:5]

            print(f"📂 Categories detected: {len(category_links)}")

            # ------------------------------
            # STEP 2 — ENTER CATEGORIES
            # ------------------------------
            for cat in category_links:

                try:
                    print(f"➡️ Entering category: {cat}")

                    page.goto(cat, timeout=60000)
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(2000)

                    # Detect grid-like structures
                    cards = page.locator(
                        "[class*=product], [class*=card], [class*=grid], [data-testid*=product]"
                    )

                    # 🚨 HARD LIMIT — prevents Amazon freeze
                    card_count = min(cards.count(), 40)

                    for i in range(card_count):

                        try:
                            c = cards.nth(i)

                            link = c.locator("a").first
                            href = link.get_attribute("href") if link else None

                            if not href:
                                continue

                            # ❌ Ignore non-product links
                            if any(x in href.lower() for x in [
                                "login", "signin", "help", "footer"
                            ]):
                                continue

                            # ✅ Product patterns
                            if any(x in href.lower() for x in [
                                "voucher", "product", "gift", "dp/"
                            ]):
                                product_links.append(urljoin(cat, href))

                        except:
                            continue

                except Exception as e:
                    print(f"⚠️ Category crawl failed: {e}")
                    continue

            browser.close()

        product_links = list(set(product_links))

        print(f"✅ Navigator V3 found {len(product_links)} REAL product links")

        return {
            "url": url,
            "product_links": product_links
        }
