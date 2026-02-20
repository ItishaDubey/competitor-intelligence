import requests


class ProductIngestionEngine:

    # =====================================================
    # SOURCE TYPE DETECTOR (NO UI CHANGE NEEDED)
    # =====================================================
    def detect_source_type(self, source):

        url = (source.get("website") or source.get("url") or "").lower()

        if "kstore" in url:
            return "kstore_api"

        if "woohoo" in url:
            return "woohoo_api"

        if "flipkart" in url:
            return "flipkart_marketplace"

        if "amazon" in url:
            return "amazon_marketplace"

        if "paytm" in url:
            return "paytm_marketplace"

        return "generic"


    # =====================================================
    # 🔥 MAIN ROUTER ENTRY (REPLACES OLD fetch())
    # =====================================================
    def fetch(self, source):

        source_type = self.detect_source_type(source)

        print(f"🧠 Source detected: {source_type}")

        # ---------- API SOURCES ----------
        if source_type in ["kstore_api", "woohoo_api"]:

            if not source.get("api"):
                print("⚠️ No API configured — skipping API ingestion")
                return []

            return self.fetch_api(source)

        # ---------- MARKETPLACES ----------
        if source_type == "flipkart_marketplace":
            return self.fetch_flipkart_marketplace(source)

        if source_type == "amazon_marketplace":
            return self.fetch_amazon_marketplace(source)

        if source_type == "paytm_marketplace":
            return self.fetch_paytm_marketplace(source)

        print("⚠️ Unknown source type — no ingestion")
        return []


    # =====================================================
    # API INGESTION (UPDATED PRICE MAPPING)
    # =====================================================
    def fetch_api(self, source):

        api = source["api"]
        print(f"📡 Fetching via API: {api}")

        res = requests.get(api, timeout=30)
        data = res.json()

        products = []

        if isinstance(data, dict):
            for key in ["products", "items", "data"]:
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break

        if not isinstance(data, list):
            print("⚠️ Unknown API structure")
            return []

        for item in data:

            name = (
                item.get("title")
                or item.get("name")
                or item.get("product_name")
                or item.get("voucherName")
            )

            # ⭐ FIXED PRICE SUPPORT (Woohoo + KStore)
            price = (
                item.get("price")
                or item.get("amount")
                or item.get("sellingPrice")
                or item.get("displayPrice")
                or item.get("faceValue")
                or item.get("denomination")
            )

            url = (
                item.get("url")
                or item.get("handle")
                or item.get("link")
            )

            if not name:
                continue

            products.append({
                "name": name,
                "price": price,
                "url": url,
                "category": item.get("category")
            })

        print(f"✅ API Products fetched: {len(products)}")

        return products


    # =====================================================
    # 🟡 FLIPKART MARKETPLACE INGESTION (PRODUCTION SAFE)
    # =====================================================
    def fetch_flipkart_marketplace(self, source):

        print("🛒 Flipkart marketplace ingestion started")

        # Flipkart blocks direct scraping — safe fallback
        return []


    # =====================================================
    # 🟡 AMAZON MARKETPLACE INGESTION
    # =====================================================
    def fetch_amazon_marketplace(self, source):

        print("🛒 Amazon marketplace ingestion started")

        # Keep empty for now — we will plug extractor later
        return []


    # =====================================================
    # 🟡 PAYTM MARKETPLACE INGESTION
    # =====================================================
    def fetch_paytm_marketplace(self, source):

        print("🛒 Paytm marketplace ingestion started")

        # Paytm uses catalog APIs — leave placeholder
        return []


    # =====================================================
    # EXISTING AUTO PAYLOAD PARSER (UNCHANGED)
    # =====================================================
    def parse_api_payloads(self, payloads):

        print("🧠 Parsing detected API payloads...")
        products = []

        def walk(obj):

            if isinstance(obj, dict):

                name = (
                    obj.get("title")
                    or obj.get("name")
                    or obj.get("productName")
                    or obj.get("productTitle")
                    or obj.get("voucherName")
                    or obj.get("displayName")
                )

                price = (
                    obj.get("price")
                    or obj.get("amount")
                    or obj.get("sellingPrice")
                    or obj.get("denomination")
                    or obj.get("amountValue")
                    or obj.get("value")
                )

                url = (
                    obj.get("url")
                    or obj.get("link")
                    or obj.get("handle")
                    or obj.get("slug")
                )

                if name:
                    products.append({
                        "name": str(name),
                        "price": price,
                        "url": url,
                        "category": obj.get("category")
                    })

                for v in obj.values():
                    walk(v)

            elif isinstance(obj, list):
                for i in obj:
                    walk(i)

        for payload in payloads:
            walk(payload)

        print(f"🔥 Parsed products from API payloads: {len(products)}")

        return products
