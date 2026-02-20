import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class Navigator:

    def discover(self, url):
        print(f"🌐 Discovering site structure: {url}")

        try:
            res = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0"
            }, timeout=20)

            soup = BeautifulSoup(res.text, "html.parser")

        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            return {"url": url, "product_links": []}

        product_links = []
        category_links = []

        # -----------------------------
        # STEP 1: Detect Product Cards
        # -----------------------------
        for a in soup.find_all("a", href=True):

            text = a.get_text(" ", strip=True).lower()
            href = urljoin(url, a["href"])

            # Ignore navigation garbage
            if any(x in text for x in ["login", "account", "cart", "help", "terms"]):
                continue

            # Detect giftcard/product patterns
            if any(x in href.lower() for x in ["product", "gift", "voucher", "card"]):
                product_links.append(href)

            # Detect category pages
            elif any(x in href.lower() for x in ["category", "digital", "gift-cards"]):
                category_links.append(href)

        # -----------------------------
        # STEP 2: Crawl Category Pages
        # -----------------------------
        for cat in category_links[:3]:  # limit depth
            try:
                r = requests.get(cat, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                s = BeautifulSoup(r.text, "html.parser")

                for a in s.find_all("a", href=True):
                    href = urljoin(cat, a["href"])

                    if any(x in href.lower() for x in ["product", "gift", "voucher"]):
                        product_links.append(href)

            except:
                pass

        print(f"✅ Navigator found {len(product_links)} product links")

        return {
            "url": url,
            "product_links": list(set(product_links))
        }
