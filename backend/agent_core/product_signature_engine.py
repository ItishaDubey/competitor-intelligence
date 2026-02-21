import re


class ProductSignatureEngine:

    BRAND_RULES = [
        ("google_play", ["google play"]),
        ("tinder", ["tinder"]),
        ("amazon", ["amazon"]),
        ("nykaa", ["nykaa"]),
        ("jio", ["jio"]),
    ]

    # =====================================================
    # SINGLE SIGNATURE EXTRACTOR
    # =====================================================
    def extract_signature(self, name: str):

        if not name:
            return "unknown"

        text = name.lower()

        # remove store breadcrumbs
        text = re.sub(r"\|.*", "", text)

        # remove noise words
        text = re.sub(
            r"(voucher|gift card|recharge code|e-gift|instant|digital)",
            "",
            text
        )

        text = re.sub(r"[^a-z0-9 ]", "", text).strip()

        # rule-based brand detection
        for sig, keywords in self.BRAND_RULES:
            for k in keywords:
                if k in text:
                    return sig

        return text.replace(" ", "_")[:40]

    # =====================================================
    # ⭐ MISSING BUILD STAGE (THIS FIXES MATCHING + PRICES)
    # =====================================================
    def build(self, products):

        if not products:
            return []

        enriched = []

        for p in products:

            name = p.get("name", "")

            p["signature"] = self.extract_signature(name)

            enriched.append(p)

        return enriched