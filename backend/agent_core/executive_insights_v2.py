class ExecutiveInsightEngineV2:

    def generate(self, baseline, competitor, competitor_name):

        baseline_signatures = {
            (p.get("signature"), p.get("variant_value"))
            for p in baseline
        }

        competitor_signatures = {
            (p.get("signature"), p.get("variant_value"))
            for p in competitor
        }

        # --------------------------------------------------
        # MATCHED + MISSING
        # --------------------------------------------------
        matched = [
            p for p in competitor
            if (p.get("signature"), p.get("variant_value"))
            in baseline_signatures
        ]

        missing = [
            p for p in competitor
            if (p.get("signature"), p.get("variant_value"))
            not in baseline_signatures
        ]

        insights = []

        # =====================================================
        # CATEGORY GAP ANALYSIS
        # =====================================================
        cat_base = {}
        cat_comp = {}

        for p in baseline:
            cat = p.get("category") or "unknown"
            cat_base[cat] = cat_base.get(cat, 0) + 1

        for p in competitor:
            cat = p.get("category") or "unknown"
            cat_comp[cat] = cat_comp.get(cat, 0) + 1

        for cat in cat_comp:

            base_count = cat_base.get(cat, 0)
            comp_count = cat_comp.get(cat, 0)

            if comp_count > base_count:

                diff = comp_count - base_count

                insights.append(
                    f"🚨 {competitor_name}: Category '{cat}' has {diff} more SKUs than baseline."
                )

        # =====================================================
        # SKU ADDITION RECOMMENDATIONS
        # =====================================================
        if missing:

            suggestions = [
                f"{m.get('name')} ({m.get('url')})"
                for m in missing[:5]
            ]

            insights.append(
                "🔥 Add high-demand SKUs:\n- " + "\n- ".join(suggestions)
            )

        return {
            "matched_count": len(matched),
            "missing_count": len(missing),
            "insights": insights
        }
