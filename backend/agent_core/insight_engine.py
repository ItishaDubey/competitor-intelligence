"""
InsightEngine v2 - Accurate AI-powered competitive insights.

Fixes:
- Uses actual scraped product data, not just diff counts
- Generates meaningful insights even when price data is sparse
- Separates "Listed but no price" from "truly not present"
- Rule-based fallback is accurate and verbose
"""

import os
import json
import re
from anthropic import Anthropic


class InsightEngine:

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("LLM_API_KEY")
        self.client = Anthropic(api_key=api_key) if api_key else None

    def generate(self, baseline_name: str, baseline_products: list,
                 competitor_name: str, diff: dict, changes: list) -> dict:
        if self.client:
            try:
                return self._ai_insights(
                    baseline_name, baseline_products,
                    competitor_name, diff, changes
                )
            except Exception as e:
                print(f"  ⚠️  AI insight failed ({e}), using rule-based fallback")

        return self._rule_based_insights(
            baseline_name, baseline_products,
            competitor_name, diff, changes
        )

    # ─────────────────────────────────────────────────────────
    # AI PATH
    # ─────────────────────────────────────────────────────────

    def _ai_insights(self, baseline_name, baseline_products,
                     competitor_name, diff, changes) -> dict:

        missing       = diff.get("missing", [])
        var_gaps      = diff.get("variant_gaps", [])
        price_diffs   = diff.get("price_diffs", [])
        matched       = diff.get("matched", [])
        recent        = [c for c in changes if c.get("competitor") == competitor_name]

        # Build compact data summaries
        missing_names = list({p.get("name") for p in missing})[:20]
        matched_names = list({p.get("name") for p in matched})[:10]
        cheaper = [p for p in price_diffs if p.get("pct_diff", 0) < -3][:8]
        pricier = [p for p in price_diffs if p.get("pct_diff", 0) > 3][:8]
        new_skus  = [c for c in recent if c["type"] == "new_sku"][:5]
        removed   = [c for c in recent if c["type"] == "removed_sku"][:5]
        repriced  = [c for c in recent if c["type"] == "price_change"][:5]

        prompt = f"""You are a senior competitive intelligence analyst for {baseline_name}, a digital gift card platform in India.

Analyse the competitive landscape vs {competitor_name} and return ONLY a JSON object with this exact structure:
{{
  "summary": "2-3 sentence executive summary of the competitive position",
  "product_gaps": ["specific product gap with context", ...],
  "variant_gaps": ["specific denomination gap", ...],
  "pricing_risks": ["specific pricing risk with numbers", ...],
  "opportunities": ["specific opportunity to exploit competitor weakness", ...],
  "recommendations": ["specific actionable recommendation", ...]
}}

DATA:
Products {competitor_name} has that {baseline_name} DOES NOT carry ({len(missing_names)} brands):
{json.dumps(missing_names, indent=2)}

Products both platforms carry ({len(matched_names)} brands):
{json.dumps(matched_names, indent=2)}

Denominations {competitor_name} offers that {baseline_name} is missing:
{json.dumps([f"{g['product_name']} – missing ₹{g['missing_variant']}" for g in var_gaps[:10]], indent=2)}

Pricing differences:
  {competitor_name} CHEAPER: {json.dumps([f"{p['product_name']} ₹{p['variant']}: their ₹{p['competitor_price']} vs your ₹{p['baseline_price']} ({p['pct_diff']:+.1f}%)" for p in cheaper], indent=2)}
  {competitor_name} PRICIER: {json.dumps([f"{p['product_name']} ₹{p['variant']}: their ₹{p['competitor_price']} vs your ₹{p['baseline_price']} ({p['pct_diff']:+.1f}%)" for p in pricier], indent=2)}

Recent {competitor_name} changes:
  New products: {json.dumps([f"{c.get('product')} at ₹{c.get('price','?')}" for c in new_skus], indent=2)}
  Removed: {json.dumps([c.get('product') for c in removed], indent=2)}
  Repriced: {json.dumps([f"{c.get('product')}: ₹{c.get('old_price')} → ₹{c.get('new_price')} ({c.get('pct_change',0):+.1f}%)" for c in repriced], indent=2)}

Be specific, data-driven, and actionable. Return ONLY valid JSON, no markdown, no extra text.
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()
        text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.DOTALL).strip()
        return json.loads(text)

    # ─────────────────────────────────────────────────────────
    # ACCURATE RULE-BASED FALLBACK
    # ─────────────────────────────────────────────────────────

    def _rule_based_insights(self, baseline_name, baseline_products,
                              competitor_name, diff, changes) -> dict:
        missing    = diff.get("missing", [])
        var_gaps   = diff.get("variant_gaps", [])
        p_diffs    = diff.get("price_diffs", [])
        matched    = diff.get("matched", [])
        recent     = [c for c in changes if c.get("competitor") == competitor_name]

        # De-duplicate missing by signature
        seen_sigs = set()
        unique_missing = []
        for p in missing:
            s = p.get("signature", "")
            if s not in seen_sigs:
                seen_sigs.add(s)
                unique_missing.append(p)

        # Categorise price diffs
        cheaper  = [p for p in p_diffs if p.get("pct_diff", 0) < -3]
        pricier  = [p for p in p_diffs if p.get("pct_diff", 0) > 3]
        new_skus = [c for c in recent if c["type"] == "new_sku"]
        removed  = [c for c in recent if c["type"] == "removed_sku"]
        repriced = [c for c in recent if c["type"] == "price_change"]

        # ── Summary ──────────────────────────────────────────
        if not unique_missing and not matched:
            summary = (
                f"Could not retrieve enough data from {competitor_name} in this scan. "
                f"Price scraping was limited — try running again with the competitor's "
                f"full gift card catalog URL for better results."
            )
        elif not unique_missing:
            summary = (
                f"{baseline_name} and {competitor_name} carry overlapping products "
                f"across {len(set(p.get('signature') for p in matched))} brands. "
                f"{'Pricing is competitive with no major gaps.' if not cheaper else f'{len(cheaper)} SKUs where {competitor_name} undercuts on price.'}"
            )
        else:
            summary = (
                f"{competitor_name} carries {len(unique_missing)} brand(s) not available on {baseline_name}, "
                f"representing a potential catalogue gap. "
                f"{'Both platforms price similarly on overlapping SKUs.' if not cheaper and not pricier else f'{len(cheaper)} SKUs where {competitor_name} is cheaper, {len(pricier)} where {baseline_name} has better pricing.'}"
            )

        # ── Product Gaps ─────────────────────────────────────
        product_gaps = []
        for p in unique_missing[:10]:
            name = p.get("name", "Unknown")
            price = p.get("price")
            if price:
                product_gaps.append(
                    f"'{name}' — available on {competitor_name} at ₹{price:,.0f}, missing from {baseline_name}"
                )
            else:
                product_gaps.append(
                    f"'{name}' — carried by {competitor_name} but not on {baseline_name}"
                )

        if not product_gaps and unique_missing:
            product_gaps = [f"'{p.get('name')}' not available on {baseline_name}" for p in unique_missing[:8]]

        # ── Variant Gaps ─────────────────────────────────────
        variant_gaps_out = [
            f"'{g['product_name']}': add ₹{g['missing_variant']:,.0f} denomination "
            f"({competitor_name} has it{'at ₹' + str(int(g['competitor_price'])) if g.get('competitor_price') else ''})"
            for g in var_gaps[:8]
        ]

        # ── Pricing Risks ─────────────────────────────────────
        pricing_risks = []
        for pd in cheaper[:6]:
            pricing_risks.append(
                f"'{pd['product_name']}' ₹{pd['variant']}: "
                f"{competitor_name} sells at ₹{pd['competitor_price']} vs your ₹{pd['baseline_price']} "
                f"({abs(pd['pct_diff']):.1f}% cheaper) — price-sensitive customers may switch"
            )

        # ── Opportunities ─────────────────────────────────────
        opportunities = []
        for pd in pricier[:4]:
            opportunities.append(
                f"'{pd['product_name']}' ₹{pd['variant']}: you price at ₹{pd['baseline_price']} "
                f"vs {competitor_name}'s ₹{pd['competitor_price']} — highlight your better value"
            )
        if new_skus:
            opportunities.append(
                f"{competitor_name} recently added {len(new_skus)} new products — "
                f"evaluate {', '.join(c.get('product','?') for c in new_skus[:3])} for inclusion"
            )
        if removed:
            opportunities.append(
                f"{competitor_name} delisted {len(removed)} products — "
                f"capture those customers if you carry these brands"
            )

        # ── Recommendations ───────────────────────────────────
        recs = []
        if unique_missing:
            top3 = [p.get('name', '?') for p in unique_missing[:3]]
            recs.append(
                f"Prioritise onboarding {len(unique_missing)} missing brands — "
                f"start with: {', '.join(top3)}"
            )
        if var_gaps:
            recs.append(
                f"Add {len(var_gaps)} denomination variants to match {competitor_name}'s range "
                f"(e.g. {var_gaps[0]['product_name']} ₹{var_gaps[0]['missing_variant']})"
            )
        if cheaper:
            recs.append(
                f"Review pricing on {len(cheaper)} undercut SKUs — "
                f"consider price matching or bundle offers to retain customers"
            )
        if repriced:
            recs.append(
                f"{competitor_name} changed prices on {len(repriced)} SKUs recently — "
                f"monitor {', '.join(c.get('product','?') for c in repriced[:2])} closely"
            )
        if not recs:
            recs.append(
                f"Run agent with {competitor_name}'s full gift card catalog URL "
                f"to get complete pricing intelligence"
            )

        return {
            "summary": summary,
            "product_gaps": product_gaps,
            "variant_gaps": variant_gaps_out,
            "pricing_risks": pricing_risks,
            "opportunities": opportunities,
            "recommendations": recs,
        }