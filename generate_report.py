"""
Clean Report Generator
Focused on what matters: products, prices, changes
"""

import json
import glob
import os
from datetime import datetime

def load_latest_digest():
    files = glob.glob('intelligence_data/digest_*.json')
    if not files:
        return None
    latest = max(files, key=os.path.getctime)
    with open(latest) as f:
        return json.load(f)

def generate_html(digest):
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Competitive Intelligence Report</title>
    <style>
        body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 1200px; 
               margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; }}
        .header p {{ margin: 10px 0 0; opacity: 0.9; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                 gap: 15px; margin-bottom: 30px; }}
        .stat {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-label {{ color: #666; font-size: 0.85em; text-transform: uppercase; }}
        .stat-value {{ font-size: 2.5em; font-weight: bold; color: #333; margin-top: 5px; }}
        .company-card {{ background: white; padding: 25px; margin-bottom: 20px; 
                        border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .company-name {{ font-size: 1.4em; font-weight: bold; margin-bottom: 15px; }}
        .baseline {{ border-left: 4px solid #667eea; }}
        .competitor {{ border-left: 4px solid #764ba2; }}
        .has-changes {{ border-left-color: #e74c3c; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
                     gap: 15px; margin: 15px 0; }}
        .info-item {{ background: #f8f9fa; padding: 15px; border-radius: 6px; }}
        .info-label {{ font-size: 0.85em; color: #666; }}
        .info-value {{ font-size: 1.3em; font-weight: bold; color: #333; margin-top: 5px; }}
        .change-badge {{ background: #e74c3c; color: white; padding: 4px 12px; 
                        border-radius: 20px; font-size: 0.85em; margin-left: 10px; }}
        .changes-section {{ background: #fff3cd; padding: 15px; margin: 15px 0; 
                           border-radius: 6px; border-left: 4px solid #ffc107; }}
        .insight-section {{ background: #d1ecf1; padding: 15px; margin: 15px 0; 
                           border-radius: 6px; border-left: 4px solid #17a2b8; }}
        .priority-high {{ border-left-color: #e74c3c; background: #f8d7da; }}
        .priority-medium {{ border-left-color: #ffc107; background: #fff3cd; }}
        .products-list {{ margin-top: 15px; }}
        .product-item {{ padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 4px; }}
        .product-name {{ font-weight: 500; }}
        .product-price {{ color: #667eea; font-weight: bold; margin-left: 10px; }}
        a {{ color: #667eea; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Competitive Intelligence Report</h1>
        <p><strong>Generated:</strong> {digest['report_date']}</p>
    </div>

    <div class="stats">
        <div class="stat">
            <div class="stat-label">Companies Monitored</div>
            <div class="stat-value">{digest['summary']['companies_monitored']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Products Tracked</div>
            <div class="stat-value">{digest['summary']['total_products_tracked']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Changes Detected</div>
            <div class="stat-value">{digest['summary']['changes_detected']}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Insights Generated</div>
            <div class="stat-value">{digest['summary']['insights_generated']}</div>
        </div>
    </div>
"""

    for result in digest.get('detailed_results', []):
        is_baseline = result.get('is_baseline', False)
        has_changes = 'changes' in result
        
        card_class = 'company-card '
        card_class += 'baseline' if is_baseline else 'competitor'
        if has_changes:
            card_class += ' has-changes'
        
        html += f"""
    <div class="{card_class}">
        <div class="company-name">
            {'🏠' if is_baseline else '🎯'} {result['company']}
            {' <span class="change-badge">CHANGES</span>' if has_changes else ''}
        </div>
        <div><a href="{result['url']}" target="_blank">{result['url']}</a></div>
        
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Products Found</div>
                <div class="info-value">{result.get('products_found', 0)}</div>
            </div>
"""
        
        if result.get('price_range'):
            pr = result['price_range']
            html += f"""
            <div class="info-item">
                <div class="info-label">Price Range</div>
                <div class="info-value">${pr['min']:.2f} - ${pr['max']:.2f}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Avg Price</div>
                <div class="info-value">${pr['avg']:.2f}</div>
            </div>
"""
        
        html += """
        </div>
"""
        
        # Changes
        if result.get('changes'):
            changes = result['changes']
            html += """
        <div class="changes-section">
            <strong>🔄 Changes Detected:</strong><br>
"""
            if changes.get('new_products'):
                html += f"<br><strong>New Products:</strong> {', '.join(changes['new_products'][:5])}"
                if len(changes['new_products']) > 5:
                    html += f" (+{len(changes['new_products'])-5} more)"
            
            if changes.get('removed_products'):
                html += f"<br><strong>Removed:</strong> {', '.join(changes['removed_products'][:5])}"
            
            if changes.get('price_changes'):
                html += "<br><strong>Price Changes:</strong><br>"
                for pc in changes['price_changes'][:5]:
                    html += f"• {pc['product']}: {pc['old_price']} → {pc['new_price']}<br>"
            
            if changes.get('avg_price_change'):
                apc = changes['avg_price_change']
                html += f"<br><strong>Average Price:</strong> ${apc['old_avg']:.2f} → ${apc['new_avg']:.2f} ({apc['change_pct']:+.1f}%)"
            
            html += """
        </div>
"""
        
        # Insights
        if result.get('insights'):
            for insight in result['insights']:
                priority = insight.get('priority', 'medium')
                html += f"""
        <div class="insight-section priority-{priority}">
            <strong>[{priority.upper()}]</strong> {insight['message']}<br>
            <em>→ {insight['recommendation']}</em>
        </div>
"""
        
        # Sample products
        if result.get('sample_products'):
            html += """
        <div class="products-list">
            <strong>Sample Products:</strong>
"""
            for product in result['sample_products']:
                price_display = f'<span class="product-price">{product.get("price", "")}</span>' if product.get('price') else ''
                html += f"""
            <div class="product-item">
                <span class="product-name">{product['name']}</span>{price_display}
            </div>
"""
            html += """
        </div>
"""
        
        html += """
    </div>
"""
    
    html += """
</body>
</html>
"""
    return html

def main():
    print("📊 Generating Report...\n")
    
    digest = load_latest_digest()
    if not digest:
        print("❌ No data found. Run the agent first:")
        print("   python competitive_intelligence_agent.py")
        return
    
    html = generate_html(digest)
    
    with open('competitive_intelligence_report.html', 'w') as f:
        f.write(html)
    
    print("✅ Report generated: competitive_intelligence_report.html")
    print("   Open it in your browser!\n")

if __name__ == "__main__":
    main()