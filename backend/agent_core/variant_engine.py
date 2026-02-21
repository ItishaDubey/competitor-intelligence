from collections import defaultdict


class VariantEngine:

    # =====================================================
    # SIGNATURE-BASED MATCHING ENGINE
    # =====================================================
    def compare(self, baseline, competitor):

        baseline_map = defaultdict(list)
        competitor_map = defaultdict(list)

        # --------------------------------------------
        # GROUP PRODUCTS BY SIGNATURE
        # --------------------------------------------
        for p in baseline:
            sig = p.get("signature")
            if sig:
                baseline_map[sig].append(p)

        for p in competitor:
            sig = p.get("signature")
            if sig:
                competitor_map[sig].append(p)

        matched = []
        missing_products = []
        variant_gaps = []
        price_diffs = []

        # --------------------------------------------
        # COMPARE LOOP
        # --------------------------------------------
        for sig, comp_variants in competitor_map.items():

            base_variants = baseline_map.get(sig)

            # ⭐ PRODUCT EXISTS ON COMPETITOR BUT NOT BASELINE
            if not base_variants:
                missing_products.extend(comp_variants)
                continue

            base_variant_values = {
                b.get("variant_value") for b in base_variants
            }

            for cv in comp_variants:

                matched.append(cv)

                # ----------------------------------------
                # VARIANT GAP DETECTION
                # ----------------------------------------
                if cv.get("variant_value") not in base_variant_values:
                    variant_gaps.append({
                        "product": cv.get("name"),
                        "signature": sig,
                        "missing_variant": cv.get("variant_value"),
                        "competitor_price": cv.get("price"),
                        "url": cv.get("url")
                    })

                # ----------------------------------------
                # PRICE DIFFERENCE DETECTION
                # ----------------------------------------
                for bv in base_variants:

                    if bv.get("variant_value") == cv.get("variant_value"):

                        bp = bv.get("price")
                        cp = cv.get("price")

                        if bp and cp and bp != cp:

                            price_diffs.append({
                                "product": cv.get("name"),
                                "variant": cv.get("variant_value"),
                                "baseline_price": bp,
                                "competitor_price": cp,
                                "url": cv.get("url")
                            })

        return {
            "matched": matched,
            "missing": missing_products,
            "variant_gaps": variant_gaps,
            "price_diffs": price_diffs
        }
