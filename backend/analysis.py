# backend/analysis.py
from datetime import datetime

def generate_strategic_brief(competitors_data, baseline_data=None):
    """
    Transforms raw scraped data into the 'Strategic Brief' format.
    """
    report = {
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "metrics": {
            "competitors_tracked": len(competitors_data),
            "total_skus": sum(c.get('product_count', 0) for c in competitors_data),
            "active_changes": 0, # Logic to track changes would go here
            "market_players": len(competitors_data) + (1 if baseline_data else 0)
        },
        "insights": [],
        "matrix": []
    }

    # Generate Matrix Rows
    # 1. Add Baseline Row
    if baseline_data:
        report['matrix'].append({
            "entity": f"🏠 {baseline_data.get('name', 'Your Company')}",
            "is_baseline": True,
            "positioning": "Baseline",
            "avg_price": baseline_data.get('price', 'N/A'),
            "catalog_depth": f"{baseline_data.get('product_count', 0)} SKUs",
            "signals": "-"
        })

    # 2. Add Competitor Rows
    base_price = baseline_data.get('price', 0) if baseline_data else 0
    
    for comp in competitors_data:
        comp_price = comp.get('price', 0) or 0
        
        # Determine Positioning (Cheaper/Parity/Premium)
        positioning = "Parity"
        if base_price and comp_price:
            diff = ((comp_price - base_price) / base_price) * 100
            if diff > 5: positioning = "Premium (+{:.0f}%)".format(diff)
            elif diff < -5: positioning = "Value ({:.0f}%)".format(diff)
            
        report['matrix'].append({
            "entity": f"🎯 {comp.get('name', 'Unknown')}",
            "is_baseline": False,
            "positioning": positioning,
            "avg_price": f"${comp_price:.2f}" if comp_price else "N/A",
            "catalog_depth": f"{comp.get('product_count', 0)} SKUs",
            "signals": "New Detected" if comp.get('product_count', 0) > 0 else "No Signal"
        })

    # Generate Insights
    # Example Logic
    report['insights'].append({
        "priority": "medium",
        "title": "Market Stability",
        "text": "No significant pricing deviations detected vs baseline this week."
    })
    
    return report