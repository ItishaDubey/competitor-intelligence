from playwright.sync_api import sync_playwright
import json


class ProductSourceResolver:

    def detect_api_products(self, url):

        print(f"🧠 Detecting hidden product APIs: {url}")

        payloads = []

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            def handle_response(response):

                try:
                    ct = response.headers.get("content-type", "")

                    if "application/json" not in ct:
                        return

                    data = response.json()

                    # ⭐ STRICT FILTER — ONLY PRODUCT DATA
                    text = json.dumps(data).lower()

                    if any(x in text for x in [
                        "denomination",
                        "variants",
                        "sellingprice",
                        "productname",
                        "voucher"
                    ]):
                        payloads.append(data)

                except:
                    pass

            page.on("response", handle_response)

            page.goto(url, timeout=60000)

            # ⭐ WAIT LONGER — APIs load async
            page.wait_for_timeout(8000)

            browser.close()

        print(f"🔥 JSON payloads captured: {len(payloads)}")

        return payloads
