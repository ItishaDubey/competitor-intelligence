"""
ProductMatcher v2 – cross-site comparison using signatures.

Fix: competitor products with no denomination (variant_value=None) are matched
by signature only, so price fills in when competitor has the same brand even
without denomination data.
"""

from collections import defaultdict


class ProductMatcher:

    def match(self, baseline: list[dict], competitor: list[dict]) -> dict:
        base_sig_index = self._index_by_sig(baseline)   # sig → [products]
        comp_sig_index = self._index_by_sig(competitor)

        matched = []
        missing = []
        variant_gaps = []
        price_diffs = []

        for sig, comp_items in comp_sig_index.items():
            base_items = base_sig_index.get(sig)

            if not base_items:
                missing.extend(comp_items)
                continue

            # Build variant map for baseline: variant_value → product
            base_var_map = {b.get("variant_value"): b for b in base_items}

            for ci in comp_items:
                matched.append(ci)
                cv = ci.get("variant_value")
                cp = ci.get("price")

                if cv is not None and cv not in base_var_map:
                    # Competitor has denomination baseline doesn't
                    variant_gaps.append({
                        "product_name": ci.get("name"),
                        "signature": sig,
                        "missing_variant": cv,
                        "competitor_price": cp,
                        "url": ci.get("url"),
                    })
                elif cv in base_var_map:
                    bp = base_var_map[cv].get("price")
                    if bp and cp:
                        try:
                            t_f, b_f = float(cp), float(bp)
                            if abs(t_f - b_f) > 0.5:
                                pct = round((t_f - b_f) / b_f * 100, 1)
                                price_diffs.append({
                                    "product_name": ci.get("name"),
                                    "variant": cv,
                                    "baseline_price": bp,
                                    "competitor_price": cp,
                                    "pct_diff": pct,
                                    "url": ci.get("url"),
                                })
                        except (TypeError, ValueError):
                            pass

        baseline_only = [
            p for sig, items in base_sig_index.items()
            if sig not in comp_sig_index
            for p in items
        ]

        prices = [p.get("price") for p in competitor if isinstance(p.get("price"), (int, float))]
        price_range = {
            "min": min(prices) if prices else None,
            "max": max(prices) if prices else None,
        }

        return {
            "matched": matched,
            "missing": missing,
            "variant_gaps": variant_gaps,
            "price_diffs": price_diffs,
            "baseline_only": baseline_only,
            "price_range": price_range,
        }

    def _index_by_sig(self, products: list[dict]) -> dict[str, list]:
        idx = defaultdict(list)
        for p in products:
            sig = p.get("signature") or "unknown"
            idx[sig].append(p)
        return dict(idx)