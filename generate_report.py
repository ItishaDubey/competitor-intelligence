"""
Professional Intelligence Report
Highlights Baseline Matches and Deep-Dive Prices
"""

import json
import glob
import os
from datetime import datetime

def load_latest_digest():
    # Load the specific 'digest_latest.json' we just saved
    try:
        with open('intelligence_data/digest_latest.json') as f: 
            return json.load(f)
    except:
        return None

def generate_html(digest):
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Strategic Intelligence Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; padding: 40px; color: #1a1a1a; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        .header {{ background: #2d3436; color: white; padding: 30px; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .meta {{ opacity: 0.7; font-size: 14px; margin-top: 5px; }}

        .baseline-card {{ background: #fff; border-left: 5px solid #0984e3; padding: 25px; margin-bottom: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        .comp-card {{ background: #fff; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); overflow: hidden; }}
        .comp-header {{ background: #dfe6e9; padding: 15px 25px; font-weight: 700; color: #2d3436; display: flex; justify-content: space-between; }}
        
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 15px 25px; color: #636e72; font-size: 12px; text-transform: uppercase; border-bottom: 2px solid #eee; }}
        td {{ padding: 15px 25px; border-bottom: 1px solid #eee; vertical-align: top; }}
        
        .price-tag {{ font-weight: 700; color: #2d3436; }}
        .match-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; background: #ffeaa7; color: #d35400; font-weight: 600; margin-bottom: 4px; }}
        .diff-pos {{ color: #d63031; font-weight: 600; font-size: 13px; }} /* Expensive */
        .diff-neg {{ color: #00b894; font-weight: 600; font-size: 13px; }} /* Cheaper */
        
        a.btn {{ display: inline-block; padding: 4px 10px; background: #eee; color: #333; text-decoration: none; border-radius: 4px; font-size: 12px; }}
        a.btn:hover {{ background: #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>Strategic Intelligence Report</h1>
                <div class="meta">Generated: {datetime.now().strftime('%B %d, %Y • %H:%M')}</div>
            </div>
        </div>

"""
    # 1. Baseline Section
    if digest.get('baseline'):
        base = digest['baseline']
        html += f"""
        <div class="baseline-card">
            <h2 style="margin-top:0; color:#0984e3;">🏠 Baseline: {base['name']}</h2>
            <p><strong>{len(base['products'])}</strong> products tracked for comparison.</p>
            <div style="display:flex; gap:10px; overflow-x:auto; padding-bottom:10px;">
        """
        for p in base['products'][:6]:
            price = f"${p['price']}" if p['price'] else "N/A"
            html += f"""
                <div style="border:1px solid #eee; padding:10px; border-radius:6px; min-width:150px;">
                    <div style="font-weight:600; font-size:14px; margin-bottom:5px;">{p['name']}</div>
                    <div style="color:#0984e3; font-weight:700;">{price}</div>
                </div>
            """
        html += "</div></div>"

    # 2. Competitors Section
    for comp in digest['competitors']:
        html += f"""
        <div class="comp-card">
            <div class="comp-header">
                <span>🎯 {comp['name']}</span>
                <span>{len(comp['products'])} Products Found</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th width="40%">Product Name</th>
                        <th width="20%">Price</th>
                        <th width="30%">Baseline Comparison</th>
                        <th width="10%">Action</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for p in comp['products']:
            price_display = f"${p['price']}" if p['price'] else "<span style='color:#b2bec3'>Click to View</span>"
            
            # Match Logic
            match_html = "-"
            if p.get('match'):
                m = p['match']
                diff_val = m['diff']
                diff_text = f"{diff_val:+.0f}%"
                diff_class = "diff-pos" if diff_val > 0 else "diff-neg"
                
                match_html = f"""
                    <div class="match-badge">⚡ MATCH FOUND</div><br>
                    Matches: <strong>{m['name']}</strong><br>
                    Diff: <span class="{diff_class}">{diff_text} vs Baseline</span>
                """

            html += f"""
                <tr>
                    <td>{p['name']}</td>
                    <td class="price-tag">{price_display}</td>
                    <td>{match_html}</td>
                    <td><a href="{p['url']}" target="_blank" class="btn">View ↗</a></td>
                </tr>
            """
            
        html += """
                </tbody>
            </table>
        </div>
        """

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
        print("✅ Report Generated: competitive_report.html")
        os.system("open competitive_report.html")
    else:
        print("❌ No data found")