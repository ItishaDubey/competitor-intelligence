from datetime import datetime


def format_price(price):
    if price is None:
        return "N/A"
    return str(price)


def generate_html(digest):

    report_date = datetime.now().strftime('%B %d, %Y • %H:%M')

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>Strategic Intelligence Report</title>
<style>
body {{
    font-family: 'Segoe UI', Arial;
    background:#f4f6f8;
    padding:40px;
}}

.container {{ max-width:1200px; margin:auto; }}

.header {{
    background:#111;
    color:#fff;
    padding:30px;
    border-radius:12px;
    margin-bottom:30px;
}}

.card {{
    background:#fff;
    border-radius:10px;
    padding:20px;
    margin-bottom:20px;
}}

.section-title {{
    font-weight:700;
    margin-top:15px;
}}

.product-row {{
    padding:8px 0;
    border-bottom:1px solid #eee;
}}

.badge {{
    background:#eee;
    padding:3px 8px;
    border-radius:6px;
    margin-left:10px;
}}
</style>
</head>
<body>
<div class="container">

<div class="header">
<h1>Strategic Intelligence Report</h1>
<div>Generated: {report_date}</div>
</div>
"""

    # -----------------------------
    # BASELINE SECTION
    # -----------------------------
    baseline = digest.get("baseline", {})
    html += f"""
<div class="card">
<h2>🏠 Baseline: {baseline.get("name","")}</h2>
<div>{len(baseline.get("products", []))} baseline products tracked</div>
</div>
"""

    # -----------------------------
    # COMPETITOR SECTION
    # -----------------------------
    for comp in digest.get("competitors", []):

        html += f"""
<div class="card">
<h2>🎯 {comp.get("name")}</h2>
<div>Price Range: {comp.get("price_range",{}).get("min")} - {comp.get("price_range",{}).get("max")}</div>
"""

        # Insights
        if comp.get("insights"):
            html += f"""
<div class="section-title">🧠 Strategic Insights</div>
<div style="white-space:pre-wrap;">{comp.get("insights")}</div>
"""

        # New Products
        if comp.get("new_products"):
            html += "<div class='section-title'>🆕 New Products (24h)</div>"
            for np in comp["new_products"]:
                html += f"<div class='product-row'>{np.get('name')}</div>"

        # Deleted Products
        if comp.get("deleted_products"):
            html += "<div class='section-title'>❌ Deleted Products</div>"
            for dp in comp["deleted_products"]:
                html += f"<div class='product-row'>{dp.get('name')}</div>"

        # Missing vs baseline
        if comp.get("missing"):
            html += "<div class='section-title'>⚠️ Missing vs Baseline</div>"
            for mp in comp["missing"][:10]:
                html += f"<div class='product-row'>{mp.get('name')}</div>"

        # Product Table
        html += "<div class='section-title'>📦 Products</div>"

        for p in comp.get("products", []):
            html += f"""
<div class="product-row">
<strong>{p.get('name')}</strong>
<span class="badge">{format_price(p.get('price'))}</span><br>
<a href="{p.get('url')}" target="_blank">{p.get('url')}</a>
</div>
"""

        html += "</div>"

    html += "</div></body></html>"
    return html


def generate_report(digest_data, output_path="competitive_report.html"):

    html = generate_html(digest_data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML Report Generated: {output_path}")
