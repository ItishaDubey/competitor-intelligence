from collections import defaultdict


class VariantEngine:

    def compare(self, baseline, competitor):

        baseline_map = defaultdict(list)
        competitor_map = defaultdict(list)

        for p in baseline:
            baseline_map[p["signature"]].append(p)

        for p in competitor:
            competitor_map[p["signature"]].append(p)

        matched = []
        missing_products = []
        variant_gaps = []
        price_comparison = []

        for sig, comp_variants in competitor_map.items():

            base_variants = baseline_map.get(sig)

            if not base_variants:
                missing_products.extend(comp_variants)
                continue

            base_variant_values = {
                b.get("variant_value") for b in base_variants
            }

            base_price_map = {
                b.get("variant_value"): b.get("price")
                for b in base_variants
            }

            for cv in comp_variants:

                matched.append(cv)

                price_comparison.append({
                    "signature": sig,
                    "product": cv["name"],
                    "variant": cv.get("variant_value"),
                    "baseline_price": base_price_map.get(
                        cv.get("variant_value")
                    ),
                    "competitor_price": cv.get("price")
                })

                if cv.get("variant_value") not in base_variant_values:
                    variant_gaps.append({
                        "product": cv["name"],
                        "missing_variant": cv.get("variant_value"),
                        "competitor_price": cv.get("price")
                    })

        return {
            "matched": matched,
            "missing": missing_products,
            "variant_gaps": variant_gaps,
            "price_comparison": price_comparison
        }
