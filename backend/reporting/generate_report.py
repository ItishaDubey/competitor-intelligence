import os
from datetime import datetime


# =====================================================
# HELPERS
# =====================================================

def safe(val):
    if val is None:
        return "-"
    return val


def build_baseline_table(baseline_products, competitors):
    """
    Build comparison table:
    Product | Variant | Competitor1 Price | Competitor2 Price
    """

    # Map competitor prices by signature + variant
    competitor_maps = {}

    for comp in competitors:
        cmap = {}
        for p in comp.get("products", []):
            key = (
                p.get("signature"),
                p.get("variant_value")
            )
            cmap[key] = p.get("price")
        competitor_maps[comp["name"]] = cmap

    rows = ""

    for bp in baseline_products:

        row = f"""
        <tr>
            <td>{bp.get('name')}</td>
            <td>{safe(bp.get('variant_value'))}</td>
        """

        for comp in competitors:
            cmap = competitor_maps.get(comp["name"], {})
            price = cmap.get(
                (bp.get("signature"), bp.get("variant_value"))
            )
            row += f"<td>{safe(price)}</td>"

        row += "</tr>"
        rows += row

    # Header
    headers = "<th>Product</th><th>Variant</th>"
    for comp in competitors:
        headers += f"<th>{comp['name']} Price</th>"

    table = f"""
    <h2>📊 Pricing Comparison</h2>
    <table class="compare">
        <thead>
            <tr>{headers}</tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """

    return table


def build_variant_section(competitors):

    html = "<h2>🔼 Variant Expansion Insights</h2>"

    for comp in competitors:

        gaps = comp.get("diff", {}).get("variant_gaps", [])

        html += f"<h3>{comp['name']}</h3>"

        if not gaps:
            html += "<p>No variant gaps detected.</p>"
            continue

        html += "<ul>"
        for g in gaps:
            html += f"""
            <li>
            {g.get('product')} — Missing Variant:
            <b>{safe(g.get('missing_variant'))}</b>
            (Competitor Price: {safe(g.get('competitor_price'))})
            </li>
            """
        html += "</ul>"

    return html


def build_changes_section(changes):

    if not changes:
        return ""

    html = "<h2>📈 Daily Changes</h2>"

    def render_list(title, items):
        if not items:
            return f"<h4>{title}: 0</h4>"

        block = f"<h4>{title}: {len(items)}</h4><ul>"
        for p in items:
            name = p.get("name") if isinstance(p, dict) else str(p)
            block += f"<li>{name}</li>"
        block += "</ul>"
        return block

    html += render_list("+ New SKUs Today", changes.get("new_skus"))
    html += render_list("- Deleted SKUs", changes.get("deleted_skus"))
    html += render_list("↓ Price Drops", changes.get("price_drops"))
    html += render_list("↑ Variant Expansion", changes.get("variant_expansion"))

    return html


def build_competitor_sections(competitors):

    html = ""

    for comp in competitors:

        diff = comp.get("diff", {})
        insights = comp.get("insights", "")

        price_range = diff.get("price_range", {})

        html += f"""
        <div class="card">
            <h2>🎯 {comp['name']}</h2>

            <p><b>Price Range:</b>
            {safe(price_range.get('min'))}
            -
            {safe(price_range.get('max'))}</p>

            <h3>🧠 Strategic Insights</h3>
            <pre>{insights}</pre>
        </div>
        """

    return html


# =====================================================
# MAIN REPORT GENERATOR
# =====================================================

def generate_report(digest):

    baseline = digest.get("baseline", {})
    competitors = digest.get("competitors", [])
    changes = digest.get("changes", {})

    baseline_products = baseline.get("products", [])

    generated_time = digest.get("generated_at", datetime.now().isoformat())

    # -------------------------------------------------
    # BUILD SECTIONS
    # -------------------------------------------------
    baseline_table = build_baseline_table(
        baseline_products,
        competitors
    )

    variant_section = build_variant_section(competitors)

    competitor_sections = build_competitor_sections(competitors)

    change_section = build_changes_section(changes)

    # -------------------------------------------------
    # HTML TEMPLATE
    # -------------------------------------------------
    html = f"""
    <html>
    <head>
    <style>

    body {{
        font-family: Arial;
        background:#f5f6f8;
        padding:40px;
    }}

    h1 {{
        background:#111;
        color:white;
        padding:20px;
        border-radius:12px;
    }}

    .card {{
        background:white;
        padding:20px;
        margin-top:20px;
        border-radius:12px;
        box-shadow:0 2px 8px rgba(0,0,0,0.08);
    }}

    table.compare {{
        width:100%;
        border-collapse:collapse;
        background:white;
        margin-top:20px;
    }}

    table.compare th, table.compare td {{
        border:1px solid #ddd;
        padding:10px;
        text-align:left;
    }}

    table.compare th {{
        background:#fafafa;
    }}

    pre {{
        white-space:pre-wrap;
        font-size:14px;
    }}

    </style>
    </head>

    <body>

    <h1>Strategic Intelligence Report</h1>
    <p>Generated: {generated_time}</p>

    <div class="card">
        <h2>🏠 Baseline: {baseline.get("name")}</h2>
        <p>{len(baseline_products)} baseline products tracked</p>
    </div>

    {baseline_table}

    {variant_section}

    {change_section}

    {competitor_sections}

    </body>
    </html>
    """

    os.makedirs("reports", exist_ok=True)

    with open("reports/competitive_report.html", "w") as f:
        f.write(html)

    print("✅ HTML Report Generated: reports/competitive_report.html")
