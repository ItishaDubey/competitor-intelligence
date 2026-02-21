import re
from backend.agent_core.product_signature_engine import ProductSignatureEngine


class ProductNormalizer:

    def __init__(self):
        self.signature_engine = ProductSignatureEngine()

    def normalize(self, raw_products):

        normalized = []

        for p in raw_products:

            name = (p.get("name") or "").strip()
            url = p.get("url")
            price = p.get("price")

            if not name:
                continue

            lowered = name.lower()

            blacklist = [
                "login", "sign in", "account", "privacy",
                "terms", "help", "footer", "wishlist",
                "support", "policy"
            ]

            if any(b in lowered for b in blacklist):
                continue

            normalized_name = self._normalize_name(name)

            signature = self.signature_engine.extract_signature(name)

            # ⭐ CRITICAL FIX — USE INGESTED VARIANT FIRST
            variant_value = (
                p.get("variant")
                or self._extract_variant(name, price)
            )

            normalized.append({
                "name": name,
                "normalized_name": normalized_name,
                "signature": signature,
                "variant_value": variant_value,
                "price": self._clean_price(price),
                "url": url,
                "category": p.get("category")
            })

        return normalized

    def _normalize_name(self, name):

        name = name.lower()
        name = re.sub(r"the official .*?\|", "", name)
        name = re.sub(r"(e gift|egift|gift card|voucher|instant voucher)", "", name)
        name = re.sub(r"\₹?\$?\d+", "", name)
        name = re.sub(r"[^a-zA-Z0-9 ]", "", name)
        name = " ".join(name.split())

        return name.strip()

    def _extract_variant(self, name, price=None):

        match = re.search(r"\₹?(\d{2,5})", str(name))
        if match:
            try:
                return int(match.group(1))
            except:
                pass

        if price:
            try:
                val = int(float(price))
                if val > 10:
                    return val
            except:
                pass

        return None

    def _clean_price(self, price):

        if price is None:
            return None

        if isinstance(price, (int, float)):
            return price

        try:
            price = re.sub(r"[^\d.]", "", str(price))
            return float(price)
        except:
            return None
