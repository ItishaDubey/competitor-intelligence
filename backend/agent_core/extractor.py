import requests
from bs4 import BeautifulSoup
import re


class Extractor:

    def extract(self, site_map):

        products = []

        for link in site_map.get("product_links", [])[:20]:  # limit for testing
            try:
                res = requests.get(link, headers={
                    "User-Agent": "Mozilla/5.0"
                }, timeout=15)

                soup = BeautifulSoup(res.text, "html.parser")

                title = soup.find("title")
                name = title.text.strip() if title else "Unknown Product"

                text = soup.get_text(" ", strip=True)

                price_match = re.search(r"(\$|₹)\s?\d+(\.\d+)?", text)
                price = price_match.group() if price_match else "N/A"

                products.append({
                    "name": name,
                    "normalized_name": self.normalize(name),
                    "price": price,
                    "url": link,
                    "category": "unknown"
                })

            except Exception as e:
                print(f"⚠️ Failed extracting {link}: {e}")

        print(f"📦 Extracted {len(products)} products")

        return products

    def normalize(self, name):
        return re.sub(r"[^a-z0-9]", "_", name.lower())
