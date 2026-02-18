"""
Professional Competitive Intelligence Report Generator
Generates Board-Ready HTML Executive Summaries.
"""

import json
import glob
import os
from datetime import datetime

class ExecutiveReportGenerator:
    def __init__(self):
        self.data_dir = 'intelligence_data'
        self.output_file = 'strategic_intelligence_brief.html'

    def load_latest_digest(self):
        files = glob.glob(os.path.join(self.data_dir, 'digest_*.json'))
        if not files:
            return None
        latest = max(files, key=os.path.getctime)
        with open(latest) as f:
            return json.load(f)

    def _generate_insight_logic(self, digest):
        """Generates rule-based strategic insights"""
        insights = []
        results = digest.get('detailed_results', [])
        baseline = next((r for r in results if r.get('is_baseline')), None)
        
        # 1. Price Positioning Analysis
        if baseline and baseline.get('price_range'):
            base_avg = baseline['price_range']['avg']
            for comp in results:
                if comp == baseline or not comp.get('price_range'): continue
                
                comp_avg = comp['price_range']['avg']
                diff = ((comp_avg - base_avg) / base_avg) * 100
                
                if diff < -10:
                    insights.append({
                        "title": "Aggressive Undercutting Detected",
                        "severity": "high",
                        "text": f"**{comp['company']}** is pricing {abs(diff):.1f}% lower than your baseline. This signals a potential loss-leader strategy or lower cost structure."
                    })
                elif diff > 10:
                    insights.append({
                        "title": "Premium Market Positioning",
                        "severity": "low",
                        "text": f"**{comp['company']}** maintains a premium position, pricing {diff:.1f}% higher. Monitor their feature set for value-add differentiators."
                    })

        # 2. Activity/Catalog Velocity
        for comp in results:
            changes = comp.get('changes', {})
            new_prods = len(changes.get('new_products', []))
            if new_prods > 2:
                insights.append({
                    "title": "Catalog Expansion Event",
                    "severity": "medium",
                    "text": f"**{comp['company']}** added {new_prods} new SKUs recently. They may be entering a new vertical or refreshing inventory."
                })

        # 3. Data Quality / Stagnation Warning (The "Zero Changes" issue you mentioned)
        zero_change_comps = [r['company'] for r in results if not r.get('changes')]
        if len(zero_change_comps) > 1:
            insights.append({
                "title": "Market Stagnation / Monitoring Alert",
                "severity": "info",
                "text": f"No activity detected for: {', '.join(zero_change_comps)}. Verify if competitors are inactive or if monitoring selectors need recalibration."
            })

        if not insights:
            insights.append({
                "title": "Market Stability",
                "severity": "low",
                "text": "No significant pricing or catalog shifts detected in this cycle. Market appears stable."
            })
            
        return insights

    def generate_html(self, digest):
        insights = self._generate_insight_logic(digest)
        results = digest.get('detailed_results', [])
        baseline = next((r for r in results if r.get('is_baseline')), None)
        competitors = [r for r in results if not r.get('is_baseline')]
        
        # Calculate Market Stats
        total_skus = sum(r.get('products_found', 0) for r in results)
        avg_market_price = 0
        prices = [r['price_range']['avg'] for r in results if r.get('price_range')]
        if prices:
            avg_market_price = sum(prices) / len(prices)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Strategic Intelligence Brief</title>
    <style>
        :root {{
            --primary: #2c3e50;
            --accent: #3498db;
            --danger: #e74c3c;
            --warning: #f1c40f;
            --success: #27ae60;
            --light: #ecf0f1;
            --text: #34495e;
            --border: #bdc3c7;
        }}
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: var(--text); background: #f8f9fa; margin: 0; padding: 40px; line-height: 1.6; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border-radius: 8px; overflow: hidden; }}
        
        /* Header */
        .header {{ background: var(--primary); color: white; padding: 40px; position: relative; }}
        .header h1 {{ margin: 0; font-weight: 300; letter-spacing: 1px; text-transform: uppercase; font-size: 24px; }}
        .header .meta {{ opacity: 0.7; font-size: 14px; margin-top: 10px; }}
        .badge {{ position: absolute; top: 40px; right: 40px; background: rgba(255,255,255,0.1); padding: 5px 15px; border-radius: 20px; font-size: 12px; letter-spacing: 1px; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.2); }}

        /* Executive Summary & Insights */
        .section {{ padding: 40px; border-bottom: 1px solid var(--light); }}
        .section-title {{ font-size: 18px; color: var(--primary); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 25px; font-weight: 700; border-left: 4px solid var(--accent); padding-left: 15px; }}
        
        .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
        .kpi-card {{ background: var(--light); padding: 20px; border-radius: 6px; text-align: center; }}
        .kpi-value {{ font-size: 32px; font-weight: 700; color: var(--primary); }}
        .kpi-label {{ font-size: 12px; text-transform: uppercase; color: #7f8c8d; letter-spacing: 1px; margin-top: 5px; }}

        .insight-card {{ border-left: 4px solid #ccc; background: #fff; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .insight-card.high {{ border-left-color: var(--danger); }}
        .insight-card.medium {{ border-left-color: var(--warning); }}
        .insight-card.low {{ border-left-color: var(--success); }}
        .insight-card.info {{ border-left-color: var(--accent); }}
        .insight-title {{ font-weight: 700; margin-bottom: 5px; display: block; }}
        
        /* Competitor Matrix */
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ text-align: left; color: #7f8c8d; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; padding: 15px; border-bottom: 2px solid var(--light); }}
        td {{ padding: 15px; border-bottom: 1px solid var(--light); vertical-align: middle; }}
        .comp-name {{ font-weight: 600; color: var(--primary); }}
        .baseline-row {{ background: #f8fbfd; }}
        .trend-up {{ color: var(--danger); font-size: 12px; }}
        .trend-down {{ color: var(--success); font-size: 12px; }}
        
        /* Footer */
        .footer {{ background: var(--light); padding: 20px 40px; text-align: center; font-size: 12px; color: #7f8c8d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">Confidential • Internal Use Only</span>
            <h1>Competitive Intelligence Brief</h1>
            <div class="meta">Generated: {datetime.now().strftime('%B %d, %Y • %H:%M')}</div>
        </div>

        <div class="section">
            <div class="section-title">Executive Summary</div>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-value">{len(competitors)}</div>
                    <div class="kpi-label">Competitors Tracked</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{total_skus}</div>
                    <div class="kpi-label">Total Products Scanned</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${avg_market_price:.2f}</div>
                    <div class="kpi-label">Avg Market Price</div>
                </div>
            </div>

            {self._render_insights(insights)}
        </div>

        <div class="section">
            <div class="section-title">Market Landscape Matrix</div>
            <table>
                <thead>
                    <tr>
                        <th>Entity</th>
                        <th>Positioning</th>
                        <th>Avg Price</th>
                        <th>Catalog Size</th>
                        <th>Recent Activity</th>
                    </tr>
                </thead>
                <tbody>
"""
        # Render Baseline Row
        if baseline:
            pr = baseline.get('price_range', {'avg': 0})
            html += f"""
                    <tr class="baseline-row">
                        <td class="comp-name">🏠 {baseline['company']} (You)</td>
                        <td><span style="background:#2c3e50; color:white; padding:2px 8px; border-radius:4px; font-size:11px;">BASELINE</span></td>
                        <td>${pr['avg']:.2f}</td>
                        <td>{baseline.get('products_found', 0)} SKUs</td>
                        <td>-</td>
                    </tr>
            """

        # Render Competitors
        for comp in competitors:
            pr = comp.get('price_range', {'avg': 0})
            
            # Calculate Positioning vs Baseline
            pos_text = "N/A"
            if baseline and baseline.get('price_range'):
                base_avg = baseline['price_range']['avg']
                diff = ((pr['avg'] - base_avg) / base_avg) * 100
                color = "var(--text)"
                if diff > 5: 
                    pos_text = f"Premium (+{diff:.0f}%)"
                    color = "var(--danger)"
                elif diff < -5: 
                    pos_text = f"Value ({diff:.0f}%)"
                    color = "var(--success)"
                else: 
                    pos_text = "Parity"

            # Activity Text
            changes = comp.get('changes', {})
            activity_text = "No recent changes"
            if changes:
                parts = []
                if 'new_products' in changes: parts.append(f"+{len(changes['new_products'])} New")
                if 'price_changes' in changes: parts.append(f"{len(changes['price_changes'])} Price Updates")
                if parts: activity_text = ", ".join(parts)

            html += f"""
                    <tr>
                        <td class="comp-name">🎯 {comp['company']}</td>
                        <td style="color:{color}; font-weight:500;">{pos_text}</td>
                        <td>${pr['avg']:.2f}</td>
                        <td>{comp.get('products_found', 0)} SKUs</td>
                        <td>{activity_text}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </div>

        <div class="footer">
            Automated Intelligence Agent v2.1 • Data is subject to scraper accuracy • <a href="#">View Raw Data</a>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _render_insights(self, insights):
        html = ""
        for i in insights:
            html += f"""
            <div class="insight-card {i['severity']}">
                <span class="insight-title">{i['title']}</span>
                {i['text']}
            </div>
            """
        return html

    def run(self):
        print("📊 Generating Strategic Brief...")
        digest = self.load_latest_digest()
        if not digest:
            print("❌ No data found. Run the agent first!")
            return

        html = self.generate_html(digest)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Report Generated: {self.output_file}")
        # Try to open automatically on Mac/Windows
        try:
            if os.name == 'nt': os.startfile(self.output_file)
            else: os.system(f'open "{self.output_file}"')
        except:
            pass

if __name__ == "__main__":
    generator = ExecutiveReportGenerator()
    generator.run()