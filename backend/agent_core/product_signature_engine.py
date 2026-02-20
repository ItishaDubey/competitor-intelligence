import re
from rapidfuzz import fuzz


class ProductSignatureEngine:

    BRAND_RULES = [
        ("google_play", ["google play"]),
        ("tinder", ["tinder"]),
        ("amazon", ["amazon"]),
        ("nykaa", ["nykaa"]),
        ("jio", ["jio"]),
    ]

    def extract_signature(self, name: str):

        if not name:
            return "unknown"

        text = name.lower()

        # Remove store breadcrumbs
        text = re.sub(r"\|.*", "", text)

        # Remove noise words
        text = re.sub(
            r"(voucher|gift card|recharge code|e-gift|instant|digital)",
            "",
            text
        )

        text = re.sub(r"[^a-z0-9 ]", "", text).strip()

        # Rule-based brand detection
        for sig, keywords in self.BRAND_RULES:
            for k in keywords:
                if k in text:
                    return sig

        # fallback signature
        return text.replace(" ", "_")[:40]
