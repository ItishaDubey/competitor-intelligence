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
                    page.wait_for_timeout(2000)

                    # -------------------------
                    # NAME
                    # -------------------------
                    name = None

                    h1 = page.locator("h1").first
                    if h1:
                        name = h1.inner_text()

                    # -------------------------
                    # PRICE
                    # -------------------------
                    price = None

                    price_text = page.locator("text=/₹|rs|inr/i").first
                    if price_text:
                        price = price_text.inner_text()

                    # -------------------------
                    # VARIANT BUTTONS
                    # -------------------------
                    variant_buttons = page.locator("button, span").all()

                    for vb in variant_buttons:
                        txt = vb.inner_text()
                        match = re.search(r"\d+", txt)

                        if match:
                            products.append({
                                "name": f"{name} {match.group(0)}",
                                "price": match.group(0),
                                "url": link
                            })

                    # fallback single product
                    if name:
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
