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

                    if "application/json" in ct:

                        data = response.json()

                        # ⭐ Only keep large payloads (likely products)
                        if isinstance(data, (list, dict)):
                            text = json.dumps(data)

                            if any(x in text.lower() for x in [
                                "price", "variant", "product", "denomination"
                            ]):
                                payloads.append(data)

                except:
                    pass

            page.on("response", handle_response)

            page.goto(url, timeout=60000)
            page.wait_for_timeout(6000)

            browser.close()

        print(f"🔥 JSON payloads captured: {len(payloads)}")

        return payloads
