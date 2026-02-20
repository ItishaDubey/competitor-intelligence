class Matcher:
    def compare(self, baseline, competitor):

        baseline_index = {
            p["normalized_name"]: p for p in baseline
        }

        matched = []
        missing = []

        prices = []

        for cp in competitor:
            prices.append(cp.get("price"))

            norm_name = cp.get("normalized_name")

            if norm_name in baseline_index:
                bp = baseline_index[norm_name]

                matched.append({
                    "name": cp.get("name"),
                    "url": cp.get("url"),
                    "price": cp.get("price"),
                    "category": cp.get("category", "unknown"),
                    "match": {
                        "name": bp.get("name"),
                        "baseline_price": bp.get("price"),
                        "competitor_price": cp.get("price")
                    }
                })
            else:
                missing.append(cp)

        # -------- PRICE RANGE --------
        numeric_prices = []
        for p in prices:
            if isinstance(p, (int, float)):
                numeric_prices.append(p)

        price_range = {
            "min": min(numeric_prices) if numeric_prices else "N/A",
            "max": max(numeric_prices) if numeric_prices else "N/A"
        }

        return {
            "matched": matched,
            "missing": missing,
            "raw_competitor_products": competitor,
            "price_range": price_range
        }
