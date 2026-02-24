"""
ReportGenerator v2 – fixes:
  1. Denomination column shows ONE clean price per row (not comma-joined)
  2. Price comparison badges render INSIDE the table cell (not below table)
  3. Product Gap section shows the correct missing products
  4. Daily changes show full detail (old price, new price, direction)
  5. Daily change cards are hyperlinked to product URLs
"""

import os
from datetime import datetime


def _safe(val, fallback="–"):
    if val is None or val == "":
        return fallback
    return str(val)


def _fmt_price(val):
    if val is None:
        return "–"
    try:
        f = float(val)
        if f == int(f):
            return f"₹{int(f):,}"
        return f"₹{f:,.2f}"
    except (TypeError, ValueError):
        return str(val)


def _pct_badge(pct, inline=False):
    if pct is None:
        return ""
    cls = "badge-up" if pct > 0 else "badge-down"
    sym = "▲" if pct > 0 else "▼"
    style = ' style="display:inline-block;margin-left:4px;"' if inline else ""
    return f'<span class="badge {cls}"{style}>{sym}{abs(pct):.1f}%</span>'


# ─────────────────────────────────────────────────────────────
# BASELINE CARD
# ─────────────────────────────────────────────────────────────

def _baseline_card(baseline):
    products = baseline.get("products", [])
    # Group by signature to show unique brands
    unique_sigs = set(p.get("signature") for p in products if p.get("signature"))
    cats = {}
    for p in products:
        c = p.get("category") or "Uncategorised"
        cats[c] = cats.get(c, 0) + 1
    cat_html = "".join(
        f'<span class="tag">{c}: {n}</span>'
        for c, n in sorted(cats.items(), key=lambda x: -x[1])[:8]
    )
    return f"""
    <div class="section-card baseline-card">
      <div class="section-title">🏠 Baseline: {_safe(baseline.get('name'))}</div>
      <p class="stat-row">
        <span class="stat-num">{len(products)}</span>
        <span class="stat-label">product variants tracked</span>
        &nbsp;·&nbsp;
        <span class="stat-num">{len(unique_sigs)}</span>
        <span class="stat-label">unique brands</span>
      </p>
      <div class="tag-row">{cat_html}</div>
    </div>
    """


# ─────────────────────────────────────────────────────────────
# PRICING MATRIX
# Rows = one per (baseline product × denomination).
# Each competitor column shows THAT denomination's price on the competitor,
# with a coloured badge if it differs from the baseline price.
# ─────────────────────────────────────────────────────────────

def _pricing_matrix(baseline_products, competitors):
    if not baseline_products:
        return "<div class='section-card'><p class='no-data'>No baseline products extracted yet.</p></div>"

    # Build per-competitor lookups
    comp_lookup = {}
    comp_sig_sets = {}
    for comp in competitors:
        exact_lk = {}
        sig_lk   = {}
        sig_set  = set()
        for p in comp.get("products", []):
            sig   = p.get("signature")
            var   = p.get("variant_value")
            entry = {"price": p.get("price"), "url": p.get("url")}
            exact_lk[(sig, var)] = entry
            sig_set.add(sig)
            sig_lk.setdefault(sig, []).append(entry)
        comp_lookup[comp["name"]] = {"exact": exact_lk, "sig": sig_lk}
        comp_sig_sets[comp["name"]] = sig_set

    # Union of all signatures present across ALL competitors
    all_comp_sigs = set()
    for s in comp_sig_sets.values():
        all_comp_sigs |= s

    # ONLY show baseline rows whose brand appears on at least one competitor
    visible = [bp for bp in baseline_products if bp.get("signature") in all_comp_sigs]

    if not visible:
        return """
        <div class='section-card'>
          <div class='section-title'>📊 Pricing Comparison Matrix</div>
          <p class='no-data'>No overlapping products found yet — run the scan again
          or check that competitor URLs point to their gift card catalogue pages.</p>
        </div>"""

    header_cols = "".join(f"<th>{c['name']} Price</th>" for c in competitors)
    header = f"<tr><th>Product</th><th>Denomination</th><th>Baseline Price</th>{header_cols}</tr>"

    rows = ""
    for bp in visible[:100]:
        sig     = bp.get("signature")
        var     = bp.get("variant_value")
        b_price = bp.get("price")

        row_cells = f"""
          <td class="product-name">{_safe(bp.get('name'))}</td>
          <td class="variant-cell">{_fmt_price(var) if var is not None else "–"}</td>
          <td class="base-price-cell">{_fmt_price(b_price)}</td>
        """

        for comp in competitors:
            lk       = comp_lookup.get(comp["name"], {})
            exact_lk = lk.get("exact", {})
            sig_list = lk.get("sig", {}).get(sig, [])

            entry = exact_lk.get((sig, var))
            if not entry:
                entry = exact_lk.get((sig, None))
            if not entry and sig_list:
                with_price = [e for e in sig_list if e.get("price")]
                if with_price and var is not None:
                    try:
                        entry = min(with_price, key=lambda e: abs(e["price"] - float(var)))
                    except Exception:
                        entry = with_price[0]
                elif with_price:
                    entry = with_price[0]
                else:
                    entry = sig_list[0]

            c_price = entry.get("price") if entry else None
            c_url   = entry.get("url")   if entry else None
            listed  = entry is not None

            cell_cls = ""
            badge    = ""
            if c_price is not None and b_price is not None:
                try:
                    diff_pct = (float(c_price) - float(b_price)) / float(b_price) * 100
                    if diff_pct < -3:
                        cell_cls = "cell-lower"
                        badge = _pct_badge(diff_pct, inline=True)
                    elif diff_pct > 3:
                        cell_cls = "cell-higher"
                        badge = _pct_badge(diff_pct, inline=True)
                except (TypeError, ValueError):
                    pass

            if c_price is not None:
                price_text = _fmt_price(c_price)
                price_display = (
                    f'<a href="{c_url}" target="_blank" class="price-link">{price_text}</a>'
                    if c_url else price_text
                )
            elif listed:
                inner = '<span class="listed-tag">Listed</span>'
                price_display = (
                    f'<a href="{c_url}" target="_blank" class="price-link">{inner}</a>'
                    if c_url else inner
                )
            else:
                price_display = "–"

            row_cells += f'<td class="{cell_cls}">{price_display}{badge}</td>'

        rows += f"<tr>{row_cells}</tr>"

    hidden = len(baseline_products) - len(visible)
    hidden_note = f" · {hidden} baseline-only products hidden" if hidden else ""

    return f"""
    <div class="section-card">
      <div class="section-title">📊 Pricing Comparison Matrix</div>
      <p class="table-note">
        <span class="badge badge-down">▼ cheaper than baseline</span>
        <span class="badge badge-up">▲ more expensive than baseline</span>
        &nbsp;Showing {len(visible)} overlapping products{hidden_note}. Click prices to open product page.
      </p>
      <div class="table-scroll">
        <table class="compare-table">
          <thead>{header}</thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>
    """




# ─────────────────────────────────────────────────────────────
# VARIANT GAP SECTION
# ─────────────────────────────────────────────────────────────

def _variant_section(competitors):
    html = '<div class="section-card"><div class="section-title">🔼 Variant Expansion Insights</div>'
    any_gaps = False
    for comp in competitors:
        gaps = comp.get("diff", {}).get("variant_gaps", [])
        html += f'<h3 class="comp-sub-title">{comp["name"]}</h3>'
        if not gaps:
            html += '<p class="no-data">No variant gaps detected.</p>'
            continue
        any_gaps = True
        html += '<ul class="gap-list">'
        for g in gaps[:20]:
            link_open  = f'<a href="{g["url"]}" target="_blank">' if g.get("url") else ""
            link_close = "</a>" if g.get("url") else ""
            html += f"""
              <li>
                {link_open}<span class="gap-product">{_safe(g.get('product_name'))}</span>{link_close}
                — missing denomination: <strong>{_fmt_price(g.get('missing_variant'))}</strong>
                <span class="comp-price">(competitor price: {_fmt_price(g.get('competitor_price'))})</span>
              </li>
            """
        html += '</ul>'
    html += "</div>"
    return html


# ─────────────────────────────────────────────────────────────
# PRODUCT GAP SECTION
# Lists products that competitor has which baseline DOES NOT carry.
# ─────────────────────────────────────────────────────────────

def _product_gap_section(competitors):
    html = '<div class="section-card"><div class="section-title">🕳️ Product Gap Analysis</div>'
    html += '<p class="table-note">Brands carried by competitors that are <strong>not on your baseline</strong>.</p>'

    for comp in competitors:
        missing = comp.get("diff", {}).get("missing", [])
        # De-duplicate by signature (1 chip per brand, not per denomination)
        seen_sigs = set()
        unique_missing = []
        for p in missing:
            s = p.get("signature") or p.get("name", "?")
            if s not in seen_sigs:
                seen_sigs.add(s)
                unique_missing.append(p)

        n = len(unique_missing)
        html += f'<h3 class="comp-sub-title">{comp["name"]} has {n} brand(s) not in baseline</h3>'

        if n == 0:
            total_comp = len(comp.get("products", []))
            if total_comp == 0:
                html += ('<p class="no-data warn-data">⚠️ No products were scraped from this competitor. '
                         'Try updating the competitor URL to their gift card catalog page '
                         '(e.g. woohoo.in/gift-cards) and run again.</p>')
            else:
                html += f'<p class="no-data">All {total_comp} scraped products match your baseline brands. '
                html += '<span class="muted-note">(If this seems wrong, check that the competitor URL covers their full catalogue.)</span></p>'
            continue

        html += '<div class="chip-grid">'
        for p in unique_missing[:30]:
            url_val = p.get("url")
            name = _safe(p.get("name"))
            price = p.get("price")
            label = name + (f' — ₹{int(price):,}' if price else "")
            if url_val:
                html += f'<a href="{url_val}" target="_blank" class="chip chip-link">{label}</a>'
            else:
                html += f'<span class="chip">{label}</span>'
        if n > 30:
            html += f'<span class="chip chip-more">+{n-30} more</span>'
        html += '</div>'

    html += "</div>"
    return html


# ─────────────────────────────────────────────────────────────
# DAILY CHANGES
# ─────────────────────────────────────────────────────────────

def _changes_section(change_data):
    no_history = '<div class="section-card"><div class="section-title">📈 Daily Changes</div><p class="no-data">No previous snapshot — changes will appear on the next run.</p></div>'
    no_changes = '<div class="section-card"><div class="section-title">📈 Daily Changes</div><p class="no-data">✅ No changes detected since last scan.</p></div>'

    if not change_data or change_data.get("status") == "first_run":
        return no_history

    changes = change_data.get("changes", [])
    if not changes:
        return no_changes

    type_cfg = {
        "new_sku":      ("🆕", "New product",   "change-new"),
        "removed_sku":  ("🗑️", "Delisted",       "change-removed"),
        "price_change": ("💰", "Price change",   "change-price"),
    }

    # Group by competitor and type for better UX
    from collections import defaultdict
    by_comp = defaultdict(lambda: defaultdict(list))
    for c in changes:
        by_comp[c.get("competitor", "Unknown")][c["type"]].append(c)

    total = len(changes)
    html = f'<div class="section-card"><div class="section-title">📈 Daily Changes ({total} detected)</div>'

    # Summary pills
    new_count    = sum(len(v.get("new_sku",[])) for v in by_comp.values() if isinstance(v, dict))
    removed_count = sum(len(v.get("removed_sku",[])) for v in by_comp.values() if isinstance(v, dict))
    price_count  = sum(len(v.get("price_change",[])) for v in by_comp.values() if isinstance(v, dict))

    html += '<div class="change-summary-pills">' 
    if new_count:    html += f'<span class="pill pill-new">🆕 {new_count} New</span>'
    if price_count:  html += f'<span class="pill pill-price">💰 {price_count} Repriced</span>'
    if removed_count: html += f'<span class="pill pill-removed">🗑️ {removed_count} Delisted</span>'
    html += '</div>'

    # Render per-competitor, type-ordered: new → price change → removed
    type_order = ["new_sku", "price_change", "removed_sku"]
    card_count = 0

    for comp_name, type_dict in by_comp.items():
        for ctype in type_order:
            comp_changes = type_dict.get(ctype, [])
            for c in comp_changes:
                if card_count >= 60:
                    break
                card_count += 1
                icon, label, cls = type_cfg.get(ctype, ("•", ctype, ""))

                if ctype == "new_sku":
                    price_str = _fmt_price(c.get("price"))
                    detail = f'Added at {price_str}' if price_str != "–" else "Newly listed"
                elif ctype == "removed_sku":
                    old = _fmt_price(c.get("old_price"))
                    detail = f'Was {old}' if old != "–" else "Delisted"
                elif ctype == "price_change":
                    pct = c.get("pct_change", 0)
                    arrow = "▲" if pct > 0 else "▼"
                    old_p = _fmt_price(c.get("old_price"))
                    new_p = _fmt_price(c.get("new_price"))
                    detail = f'{old_p} → {new_p} {arrow}{abs(pct):.1f}%'
                else:
                    detail = ""

                url = c.get("url") or ""
                product_name = _safe(c.get("product"))
                if url:
                    product_html = f'<a href="{url}" target="_blank" class="change-link">{product_name} ↗</a>'
                else:
                    product_html = product_name

                if card_count == 1:
                    html += '<div class="changes-grid">'

                html += f"""
                  <div class="change-item {cls}">
                    <span class="change-icon">{icon}</span>
                    <div class="change-body">
                      <div class="change-comp">{_safe(comp_name)} · {label}</div>
                      <div class="change-product">{product_html}</div>
                      <div class="change-detail">{detail}</div>
                    </div>
                  </div>
                """

    if card_count > 0:
        html += '</div>'

    remaining = total - min(card_count, 60)
    if remaining > 0:
        html += f'<p class="table-note" style="margin-top:12px">+ {remaining} more changes not shown.</p>'

    html += "</div>"
    return html


# ─────────────────────────────────────────────────────────────
# INSIGHT CARD
# ─────────────────────────────────────────────────────────────

def _insight_card(comp):
    insights = comp.get("insights", {})
    if isinstance(insights, str):
        return f"""
        <div class="section-card insight-card">
          <div class="section-title">🎯 {comp['name']}</div>
          <pre class="insight-text">{insights}</pre>
        </div>
        """

    def _bullets(items, cls=""):
        if not items:
            return '<p class="no-data">None identified.</p>'
        return (
            "<ul class='insight-list " + cls + "'>" +
            "".join(f"<li>{item}</li>" for item in items) +
            "</ul>"
        )

    diff = comp.get("diff", {})
    price_range   = diff.get("price_range", {})
    matched_count = len(diff.get("matched", []))
    missing_count = len(set(p.get("signature") for p in diff.get("missing", [])))  # unique brands

    return f"""
    <div class="section-card insight-card">
      <div class="section-title">🎯 {comp['name']}</div>

      <div class="insight-stats">
        <div class="istat">
          <span class="istat-num">{matched_count}</span>
          <span class="istat-lbl">Matched SKUs</span>
        </div>
        <div class="istat">
          <span class="istat-num">{missing_count}</span>
          <span class="istat-lbl">Brands Baseline Is Missing</span>
        </div>
        <div class="istat">
          <span class="istat-num">{_fmt_price(price_range.get('min'))}–{_fmt_price(price_range.get('max'))}</span>
          <span class="istat-lbl">Price Range</span>
        </div>
      </div>

      <p class="insight-summary">{_safe(insights.get('summary', ''))}</p>

      <div class="insight-grid">
        <div class="insight-col">
          <div class="insight-col-title">🕳️ Product Gaps</div>
          {_bullets(insights.get('product_gaps', []))}
        </div>
        <div class="insight-col">
          <div class="insight-col-title">↔️ Variant Gaps</div>
          {_bullets(insights.get('variant_gaps', []))}
        </div>
        <div class="insight-col">
          <div class="insight-col-title">⚠️ Pricing Risks</div>
          {_bullets(insights.get('pricing_risks', []), 'risk-list')}
        </div>
        <div class="insight-col">
          <div class="insight-col-title">✅ Recommendations</div>
          {_bullets(insights.get('recommendations', []), 'rec-list')}
        </div>
      </div>
    </div>
    """


# ─────────────────────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────────────────────

def generate_report(digest: dict, output_path: str = "reports/competitive_report.html"):

    baseline    = digest.get("baseline", {})
    competitors = digest.get("competitors", [])
    changes     = digest.get("changes", {})
    generated   = digest.get("generated_at", datetime.now().isoformat())

    baseline_products = baseline.get("products", [])

    sections  = _baseline_card(baseline)
    sections += _pricing_matrix(baseline_products, competitors)
    sections += _variant_section(competitors)
    sections += _product_gap_section(competitors)
    sections += _changes_section(changes)
    sections += "".join(_insight_card(c) for c in competitors)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Strategic Intelligence Report</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:      #f0f2f7;
  --surface: #ffffff;
  --border:  #e3e7ef;
  --primary: #2d3a8c;
  --accent:  #4f6ef7;
  --success: #1aab6d;
  --danger:  #e34b4b;
  --text:    #1a1f36;
  --muted:   #6b7391;
  --radius:  14px;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text)}}

.report-header{{
  background:linear-gradient(135deg,#1a2050 0%,#2d3a8c 60%,#4f6ef7 100%);
  color:#fff;padding:48px 56px 40px
}}
.report-header h1{{
  font-family:'DM Serif Display',serif;font-size:2.6rem;font-weight:400;
  letter-spacing:-.5px;line-height:1.1;margin-bottom:8px
}}
.report-header .meta{{font-size:.9rem;opacity:.7;letter-spacing:.5px}}

.report-body{{
  max-width:1280px;margin:0 auto;padding:40px 48px 80px;
  display:flex;flex-direction:column;gap:24px
}}

.section-card{{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:28px 32px;
  box-shadow:0 1px 4px rgba(0,0,0,.04)
}}
.section-title{{
  font-size:1.2rem;font-weight:700;color:var(--primary);
  margin-bottom:20px;padding-bottom:12px;
  border-bottom:2px solid var(--border);letter-spacing:-.2px
}}
.comp-sub-title{{font-size:1rem;font-weight:600;color:var(--text);margin:20px 0 10px}}

/* Baseline */
.stat-row{{display:flex;align-items:baseline;gap:8px;margin-bottom:14px;flex-wrap:wrap}}
.stat-num{{font-size:2.4rem;font-weight:700;color:var(--primary);font-family:'DM Serif Display',serif}}
.stat-label{{font-size:1rem;color:var(--muted)}}
.tag-row{{display:flex;flex-wrap:wrap;gap:8px}}
.tag{{background:#eef1ff;color:var(--primary);font-size:.78rem;font-weight:600;padding:4px 12px;border-radius:20px}}

/* Table */
.table-scroll{{overflow-x:auto;margin-top:8px}}
.compare-table{{width:100%;border-collapse:collapse;font-size:.87rem}}
.compare-table th{{
  background:#f6f8fe;border:1px solid var(--border);padding:10px 14px;
  text-align:left;font-weight:600;color:var(--primary);white-space:nowrap
}}
.compare-table td{{
  border:1px solid var(--border);padding:9px 14px;
  font-family:'JetBrains Mono',monospace;font-size:.84rem;color:var(--text)
}}
.compare-table tbody tr:hover td{{background:#f9faff}}
.product-name{{font-family:'DM Sans',sans-serif!important;font-weight:500;font-size:.9rem!important}}
.variant-cell,.base-price-cell{{color:var(--muted);font-size:.82rem!important}}
.cell-lower{{color:var(--danger);font-weight:600}}
.cell-higher{{color:var(--success);font-weight:600}}
.price-link{{color:inherit;text-decoration:none;border-bottom:1px dashed currentColor}}
.price-link:hover{{text-decoration:underline}}
.listed-tag{{
  display:inline-block;font-size:.72rem;font-weight:600;
  background:#eef4ff;color:#4f6ef7;border:1px solid #c7d2fe;
  padding:1px 7px;border-radius:10px;
}}

/* Badges */
.badge{{
  display:inline-block;font-size:.72rem;font-weight:700;
  padding:2px 6px;border-radius:4px;
  font-family:'JetBrains Mono',monospace
}}
.badge-down{{background:#fce8e8;color:var(--danger)}}
.badge-up{{background:#e6f9f0;color:var(--success)}}
.table-note{{margin-bottom:12px;font-size:.8rem;color:var(--muted);display:flex;gap:12px;align-items:center;flex-wrap:wrap}}

/* Gap lists */
.gap-list{{list-style:none;display:flex;flex-direction:column;gap:6px}}
.gap-list li{{
  font-size:.9rem;padding:8px 12px;background:#f8f9ff;
  border-left:3px solid var(--accent);border-radius:0 8px 8px 0
}}
.gap-product{{font-weight:600}}
.comp-price{{color:var(--muted);font-size:.84rem;margin-left:4px}}
.no-data{{color:var(--muted);font-size:.9rem;font-style:italic}}

/* Chip grid (product gaps) */
.chip-grid{{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}}
.chip{{
  background:#eef1ff;color:var(--primary);font-size:.8rem;
  font-weight:500;padding:5px 14px;border-radius:20px
}}
.chip-link{{text-decoration:none;transition:background .15s}}
.chip-link:hover{{background:#c7d2fe}}
.chip-more{{background:#f0f0f0;color:#888}}

/* Daily changes */
.changes-grid{{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));
  gap:12px;margin-top:4px
}}
.change-item{{
  display:flex;gap:12px;align-items:flex-start;
  padding:12px 16px;border-radius:10px;border:1px solid var(--border)
}}
.change-new    {{background:#f0fff7;border-color:#a7f3d0}}
.change-removed{{background:#fff5f5;border-color:#fca5a5}}
.change-price  {{background:#fffbf0;border-color:#fcd34d}}
.change-icon{{font-size:1.4rem;flex-shrink:0}}
.change-comp   {{font-size:.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}}
.change-product{{font-size:.9rem;font-weight:600;margin:3px 0}}
.change-detail {{font-size:.82rem;font-family:'JetBrains Mono',monospace;color:var(--muted)}}
.change-link   {{color:var(--accent);text-decoration:none;font-weight:700}}
.change-link:hover{{text-decoration:underline}}

/* Insight card */
.insight-stats{{display:flex;gap:32px;margin-bottom:20px;padding-bottom:20px;border-bottom:1px solid var(--border);flex-wrap:wrap}}
.istat{{display:flex;flex-direction:column;gap:2px}}
.istat-num{{font-size:1.6rem;font-weight:700;color:var(--primary);font-family:'DM Serif Display',serif;line-height:1}}
.istat-lbl{{font-size:.78rem;color:var(--muted)}}
.insight-summary{{
  font-size:.95rem;color:var(--text);background:#f6f8fe;
  border-left:4px solid var(--accent);padding:12px 16px;
  border-radius:0 8px 8px 0;margin-bottom:20px;line-height:1.6
}}
.insight-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
@media(max-width:900px){{.insight-grid{{grid-template-columns:1fr}}}}
.insight-col-title{{font-size:.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin-bottom:10px}}
.insight-list{{list-style:none;display:flex;flex-direction:column;gap:6px}}
.insight-list li{{font-size:.88rem;padding:6px 10px 6px 14px;border-left:3px solid var(--border);line-height:1.45;border-radius:0 4px 4px 0}}
.risk-list li{{border-color:var(--danger);background:#fff9f9}}
.rec-list  li{{border-color:var(--success);background:#f3fdf8}}
.insight-text{{white-space:pre-wrap;font-family:'DM Sans',sans-serif;font-size:.9rem;line-height:1.7}}
</style>
</head>
<body>
<header class="report-header">
  <h1>Strategic Intelligence Report</h1>
  <p class="meta">Generated: {generated} &nbsp;|&nbsp; {len(competitors)} competitor(s) analysed</p>
</header>
<main class="report-body">
  {sections}
</main>
</body>
</html>
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    print(f"✅ Report saved → {output_path}")
    return output_path