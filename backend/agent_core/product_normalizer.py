import re
from backend.agent_core.product_signature_engine import ProductSignatureEngine


class ProductNormalizer:

    # ----------------------------------------------------
    # INIT — attach Signature Engine
    # ----------------------------------------------------
    def __init__(self):
        self.signature_engine = ProductSignatureEngine()

    # ----------------------------------------------------
    # Clean + Normalize Raw Extracted Products
    # ----------------------------------------------------
    def normalize(self, raw_products):

        normalized = []

        for p in raw_products:

            name = (p.get("name") or "").strip()
            url = p.get("url")
            price = p.get("price")

            # ---------------------------
            # HARD FILTERS (kills garbage)
            # ---------------------------
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

            # ---------------------------
            # Normalize Name
            # ---------------------------
            normalized_name = self._normalize_name(name)

            # ---------------------------
            # ⭐ PRODUCT SIGNATURE
            # ---------------------------
            signature = self.signature_engine.extract_signature(name)

            # ---------------------------
            # Detect Variant Value (₹500 etc)
            # ---------------------------
            variant_value = self._extract_variant(name)

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

    # ----------------------------------------------------
    # Normalize Product Name  ⭐ FIXED INDENTATION
    # ----------------------------------------------------
    def _normalize_name(self, name):

        name = name.lower()

        # ⭐ REMOVE KSTORE BRAND PREFIX
        name = re.sub(r"the official .*?\|", "", name)

        # remove currency values
        name = re.sub(r"\₹?\$?\d+", "", name)

        # remove punctuation
        name = re.sub(r"[^a-zA-Z0-9 ]", "", name)

        # collapse spaces
        name = re.sub(r"\s+", " ", name)

        name = name.strip()

        return name

    # ----------------------------------------------------
    # Extract Variant Value (50 / 100 / 500 etc)
    # ----------------------------------------------------
    def _extract_variant(self, name):

        match = re.search(r"\₹?(\d+)", name)
        if match:
            try:
                return int(match.group(1))
            except:
                return None

        return None

    # ----------------------------------------------------
    # Clean Price Field
    # ----------------------------------------------------
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
