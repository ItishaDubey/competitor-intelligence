import requests


class ProductIngestionEngine:

    # =====================================================
    # SOURCE TYPE DETECTOR
    # =====================================================
    def detect_source_type(self, source):

        url = (source.get("website") or source.get("url") or "").lower()

        if "kstore" in url:
            return "kstore_api"

        if "woohoo" in url:
            return "woohoo_api"

        return "generic"


    # =====================================================
    # MAIN ENTRY
    # =====================================================
    def fetch(self, source):

        source_type = self.detect_source_type(source)

        print(f"🧠 Source detected: {source_type}")

        if source_type in ["kstore_api", "woohoo_api"]:

            if not source.get("api"):
                print("⚠️ No API configured")
                return []

            return self.fetch_api(source)

        return []


    # =====================================================
    # ⭐ FIXED API INGESTION
    # =====================================================
    def fetch_api(self, source):

        api = source["api"]

        print(f"📡 Fetching API: {api}")

        res = requests.get(api, timeout=30)
        data = res.json()

        products = []

        # unwrap payload
        if isinstance(data, dict):
            for key in ["products", "items", "data"]:
                if key in data:
                    data = data[key]
                    break

        if not isinstance(data, list):
            print("⚠️ Unknown API structure")
            return []

        for item in data:

            name = (
                item.get("title")
                or item.get("name")
                or item.get("voucherName")
                or item.get("displayName")
            )

            url = (
                item.get("url")
                or item.get("link")
                or item.get("handle")
            )

            # 🔥 CRITICAL — HANDLE DENOMINATIONS
            variants = (
                item.get("denominations")
                or item.get("variants")
                or item.get("values")
            )

            # CASE 1 — denomination list
            if isinstance(variants, list):

                for v in variants:

                    price = (
                        v.get("price")
                        or v.get("value")
                        or v.get("amount")
                        or v
                    )

                    products.append({
                        "name": str(name),
                        "price": price,
                        "variant": price,
                        "url": url,
                        "category": item.get("category")
                    })

            else:

                price = (
                    item.get("price")
                    or item.get("amount")
                    or item.get("sellingPrice")
                    or item.get("displayPrice")
                )

                products.append({
                    "name": str(name),
                    "price": price,
                    "variant": price,
                    "url": url,
                    "category": item.get("category")
                })

        print(f"🔥 API products parsed: {len(products)}")

        return products
    # =====================================================
# ⭐ DOM PRICE FALLBACK (RESTORES OLD BEHAVIOR)
# =====================================================
    def dom_price_fallback(self, url):

        from playwright.sync_api import sync_playwright

        print("🧩 Running DOM fallback extractor...")

        products = []

        try:
            with sync_playwright() as p:

                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto(url, timeout=60000)
                page.wait_for_timeout(5000)

                items = page.evaluate("""
                () => {
                    const out = [];
                    const els = document.querySelectorAll("h1,h2,h3,h4,div,span,a");

                    els.forEach(el => {
                        const text = el.innerText;
                        if(!text) return;

                        const priceMatch = text.match(/[₹$]\\s?\\d+/);
                        if(priceMatch){
                            out.push({
                                name: text.trim(),
                                price: priceMatch[0]
                            });
                        }
                    });
                    return out;
                }
                """)

                browser.close()

                for i in items:
                    products.append({
                        "name": i.get("name"),
                        "price": i.get("price"),
                        "url": url
                    })
        except Exception as e:
            print("⚠️ DOM fallback failed:", e)

        print(f"🧩 DOM fallback products: {len(products)}")
        return products


    # =====================================================
    # ⭐ FIXED PAYLOAD PARSER (INSIDE CLASS NOW)
    # =====================================================
    def parse_api_payloads(self, payloads):

        print("🧠 Parsing detected API payloads...")
        products = []

        def walk(obj):

            if isinstance(obj, dict):

                name = (
                    obj.get("title")
                    or obj.get("name")
                    or obj.get("voucherName")
                    or obj.get("displayName")
                )

                url = (
                    obj.get("url")
                    or obj.get("link")
                    or obj.get("handle")
                )

                variants = (
                    obj.get("denominations")
                    or obj.get("variants")
                    or obj.get("values")
                )

                price = (
                    obj.get("price")
                    or obj.get("amount")
                    or obj.get("value")
                )

                if name:

                    if isinstance(variants, list):

                        for v in variants:
                            v_price = (
                                v.get("price")
                                or v.get("value")
                                or v
                            )

                            products.append({
                                "name": name,
                                "price": v_price,
                                "variant": v_price,
                                "url": url
                            })

                    else:

                        products.append({
                            "name": name,
                            "price": price,
                            "variant": price,
                            "url": url
                        })

                for val in obj.values():
                    walk(val)

            elif isinstance(obj, list):
                for i in obj:
                    walk(i)

        for payload in payloads:
            walk(payload)

        print(f"🔥 Payload products parsed: {len(products)}")

        return products