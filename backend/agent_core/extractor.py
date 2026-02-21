from playwright.sync_api import sync_playwright
import re


class Extractor:

    def extract(self, site_map):

        print("📦 Extracting product details...")

        products = []

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for link in site_map["product_links"]:

                try:
                    page.goto(link, timeout=60000)
                    page.wait_for_timeout(2500)

                    # -------------------------------------------------
                    # PRODUCT NAME (STRICT)
                    # -------------------------------------------------
                    name = None

                    h1 = page.locator("h1").first

                    if h1.count() > 0:
                        name = h1.inner_text().strip()

                    if not name:
                        continue

                    # -------------------------------------------------
                    # VARIANT / DENOMINATION DETECTION ⭐
                    # Only look inside product container
                    # -------------------------------------------------
                    variant_values = set()

                    variant_nodes = page.locator(
                        "button:has-text('₹'), span:has-text('₹'), div:has-text('₹')"
                    ).all()

                    for node in variant_nodes:

                        try:
                            txt = node.inner_text()

                            match = re.search(r"\₹?\s?(\d{2,5})", txt)

                            if match:
                                val = int(match.group(1))

                                # avoid crazy numbers like 999999
                                if 10 <= val <= 50000:
                                    variant_values.add(val)

                        except:
                            pass

                    # -------------------------------------------------
                    # PRICE EXTRACTION ⭐
                    # Try strong selectors first
                    # -------------------------------------------------
                    price = None

                    price_locators = [
                        "[class*=price]",
                        "[class*=amount]",
                        "[class*=value]"
                    ]

                    for sel in price_locators:
                        el = page.locator(sel).first
                        if el.count() > 0:
                            txt = el.inner_text()
                            m = re.search(r"\₹?\s?([\d,]+)", txt)
                            if m:
                                price = m.group(1)
                                break

                    # -------------------------------------------------
                    # BUILD PRODUCTS
                    # -------------------------------------------------
                    if variant_values:

                        for v in variant_values:

                            products.append({
                                "name": f"{name} {v}",
                                "price": v,       # denomination = price
                                "url": link
                            })

                    else:
                        products.append({
                            "name": name,
                            "price": price,
                            "url": link
                        })

                except Exception as e:
                    print(f"⚠️ Extract error: {e}")

            browser.close()

        print(f"📦 Extracted {len(products)} products")

        return products
