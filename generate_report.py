"""
Professional Intelligence Report Generator
Reads 'intelligence_data/digest_latest.json' and creates a clean HTML report.
"""

import json
import os
from datetime import datetime

def load_latest_digest():
    path = 'intelligence_data/digest_latest.json'
    if os.path.exists(path):
        with open(path) as f: return json.load(f)
    return None

def format_price(price):
    if price is None or price == "N/A": return "N/A"
    try:
        # If it's already a number
        if isinstance(price, (int, float)):
            return f"{price:.2f}"
        # If it's a string, just return it
        return str(price)
    except:
        return "N/A"

def generate_html(digest):
    report_date = datetime.now().strftime('%B %d, %Y • %H:%M')
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Strategic Intelligence Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 40px; color: #1a1a1a; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        /* Header */
        .header {{ background: linear-gradient(135deg, #2d3436 0%, #000000 100%); color: white; padding: 40px; border-radius: 12px; margin-bottom: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; letter-spacing: -0.5px; }}
        .meta {{ opacity: 0.6; font-size: 14px; margin-top: 8px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }}

        /* Baseline Card */
        .baseline-card {{ background: #fff; border-left: 5px solid #0984e3; padding: 30px; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .baseline-title {{ margin: 0 0 15px 0; color: #0984e3; font-size: 18px; display: flex; align-items: center; gap: 10px; }}
        .product-scroller {{ display: flex; gap: 15px; overflow-x: auto; padding-bottom: 10px; }}
        .mini-card {{ border: 1px solid #eee; padding: 12px; border-radius: 8px; min-width: 160px; background: #fafafa; }}
        
        /* Competitor Card */
        .comp-card {{ background: #fff; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #eee; }}
        .comp-header {{ background: #f8f9fa; padding: 20px 30px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
        .comp-name {{ font-weight: 700; color: #2d3436; font-size: 18px; }}
        .comp-count {{ background: #dfe6e9; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; color: #636e72; }}
        
        /* Table */
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 15px 30px; color: #b2bec3; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; border-bottom: 1px solid #eee; }}
        td {{ padding: 20px 30px; border-bottom: 1px solid #f5f5f5; vertical-align: middle; }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover td {{ background: #fbfbfb; }}
        
        .product-name {{ font-weight: 600; color: #2d3436; display: block; margin-bottom: 4px; }}
        .product-url {{ font-size: 12px; color: #b2bec3; text-decoration: none; }}
        .price-tag {{ font-family: 'Consolas', monospace; font-weight: 700; color: #2d3436; background: #eee; padding: 6px 10px; border-radius: 6px; font-size: 14px; display: inline-block; }}
        
        /* Match Badges */
        .match-box {{ font-size: 13px; line-height: 1.5; }}
        .match-label {{ display: inline-flex; align-items: center; gap: 5px; padding: 4px 8px; border-radius: 4px; font-size: 11px; background: #fff3cd; color: #856404; font-weight: 700; margin-bottom: 6px; }}
        .diff-pos {{ color: #e74c3c; font-weight: 700; }} /* More Expensive */
        .diff-neg {{ color: #27ae60; font-weight: 700; }} /* Cheaper */
        
        .btn {{ display: inline-block; padding: 8px 16px; background: #fff; border: 1px solid #dfe6e9; color: #636e72; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: 600; transition: all 0.2s; }}
        .btn:hover {{ border-color: #b2bec3; color: #2d3436; background: #f5f6fa; }}
        
        .empty-state {{ padding: 40px; text-align: center; color: #b2bec3; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Strategic Intelligence Report</h1>
            <div class="meta">Generated: {report_date}</div>
        </div>
"""

    # 1. Baseline Section
    if digest.get('baseline') and digest['baseline'].get('products'):
        base = digest['baseline']
        html += f"""
        <div class="baseline-card">
            <h2 class="baseline-title">🏠 Baseline: {base['name']}</h2>
            <div class="product-scroller">
        """
        for p in base['products'][:10]: # Show max 10 baseline items
            price = format_price(p.get('price'))
            name = p.get('name', 'Unknown Product')
            html += f"""
                <div class="mini-card">
                    <div style="font-weight:600; font-size:13px; margin-bottom:5px; height:40px; overflow:hidden;">{name[:40]}...</div>
                    <div style="color:#0984e3; font-weight:700;">{price}</div>
                </div>
            """
        html += "</div></div>"

    # 2. Competitors Section
    for comp in digest.get('competitors', []):
        products = comp.get('products', [])
        html += f"""
        <div class="comp-card">
            <div class="comp-header">
                <span class="comp-name">🎯 {comp['name']}</span>
                <span class="comp-count">{len(products)} Products Found</span>
            </div>
        """
        
        if not products:
            html += '<div class="empty-state">No products detected. Check the URL or site structure.</div>'
        else:
            html += """
            <table>
                <thead>
                    <tr>
                        <th width="45%">Product Details</th>
                        <th width="15%">Price</th>
                        <th width="25%">Comparison</th>
                        <th width="15%" style="text-align:right">Action</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for p in products:
                name = p.get('name', 'Unknown Product')
                url = p.get('url', '#')
                price_display = format_price(p.get('price'))
                
                # Match Logic
                match_html = '<span style="color:#dfe6e9; font-size:12px;">-</span>'
                if p.get('match'):
                    m = p['match']
                    diff_val = m.get('diff', 0)
                    
                    if diff_val > 0:
                        diff_span = f'<span class="diff-pos">+{diff_val:.0f}% vs Yours</span>'
                    elif diff_val < 0:
                        diff_span = f'<span class="diff-neg">{diff_val:.0f}% vs Yours</span>'
                    else:
                        diff_span = '<span style="color:#b2bec3">Price Parity</span>'
                        
                    match_html = f"""
                        <div class="match-box">
                            <span class="match-label">⚡ MATCH</span><br>
                            Matched to: <strong>{m.get('name', 'Unknown')[:30]}...</strong><br>
                            {diff_span}
                        </div>
                    """

                html += f"""
                <tr>
                    <td>
                        <span class="product-name">{name}</span>
                        <a href="{url}" target="_blank" class="product-url">{url[:60]}...</a>
                    </td>
                    <td><span class="price-tag">{price_display}</span></td>
                    <td>{match_html}</td>
                    <td style="text-align:right">
                        <a href="{url}" target="_blank" class="btn">View Page ↗</a>
                    </td>
                </tr>
                """
            html += "</tbody></table>"
            
        html += "</div>"

    html += """
    </div>
</body>
</html>
"""
    return html

if __name__ == "__main__":
    digest = load_latest_digest()
    if digest:
        with open('competitive_report.html', 'w', encoding='utf-8') as f:
            f.write(generate_html(digest))
        print("✅ HTML Report Generated: competitive_report.html")
    else:
        print("❌ No data found in 'intelligence_data/digest_latest.json'. Run the agent first.")