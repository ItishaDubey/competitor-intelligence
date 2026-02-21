from collections import defaultdict


class ProductMatcher:

    # =====================================================
    # MATCH PRODUCTS USING SIGNATURE
    # =====================================================
    def match(self, baseline_products, competitor_products):

        matched = []
        missing_from_baseline = []     # ⭐ competitor SKUs baseline doesn't have
        variant_gaps = []

        # -------------------------------------------------
        # BUILD INDEXES BY SIGNATURE
        # -------------------------------------------------
        base_index = defaultdict(list)
        comp_index = defaultdict(list)

        for bp in baseline_products:
            sig = bp.get("signature")
            if sig:
                base_index[sig].append(bp)

        for cp in competitor_products:
            sig = cp.get("signature")
            if sig:
                comp_index[sig].append(cp)

        # -------------------------------------------------
        # MATCH LOOP — BASELINE vs COMPETITOR
        # -------------------------------------------------
        for sig, base_items in base_index.items():

            comp_items = comp_index.get(sig, [])

            if not comp_items:
                continue

            base_variants = {
                b.get("variant_value") for b in base_items
            }

            for cp in comp_items:

                matched.append(cp)

                if cp.get("variant_value") not in base_variants:

                    variant_gaps.append({
                        "product": cp.get("name"),
                        "missing_variant": cp.get("variant_value"),
                        "competitor_price": cp.get("price"),
                        "url": cp.get("url")
                    })

        # -------------------------------------------------
        # COMPETITOR PRODUCTS NOT IN BASELINE ⭐
        # -------------------------------------------------
        for sig, comp_items in comp_index.items():
            if sig not in base_index:
                missing_from_baseline.extend(comp_items)

        # -------------------------------------------------
        # PRICE RANGE
        # -------------------------------------------------
        prices = [
            p.get("price")
            for p in competitor_products
            if isinstance(p.get("price"), (int, float))
        ]

        price_range = {}
        if prices:
            price_range = {
                "min": min(prices),
                "max": max(prices)
            }

        return {
            "matched": matched,
            "missing": missing_from_baseline,
            "variant_gaps": variant_gaps,
            "price_range": price_range
        }
