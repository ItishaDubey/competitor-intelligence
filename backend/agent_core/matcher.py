from rapidfuzz import fuzz


class Matcher:

    # ----------------------------------------------------
    # Find Best Fuzzy Match
    # ----------------------------------------------------
    def _find_match(self, name, baseline_products):

        best_match = None
        best_score = 0

        for bp in baseline_products:

            score = fuzz.token_set_ratio(
                name,
                bp.get("normalized_name", "")
            )

            if score > best_score:
                best_score = score
                best_match = bp

        if best_score > 80:
            return best_match

        return None

    # ----------------------------------------------------
    # Compare baseline vs competitor
    # ----------------------------------------------------
    def compare(self, baseline, competitor):

        matched = []
        missing = []

        prices = []

        for cp in competitor:

            prices.append(cp.get("price"))

            norm_name = cp.get("normalized_name", "")

            bp = self._find_match(norm_name, baseline)

            if bp:

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
        numeric_prices = [
            p for p in prices if isinstance(p, (int, float))
        ]

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
