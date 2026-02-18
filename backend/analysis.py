from datetime import datetime

def generate_strategic_brief(competitors_data, baseline_data=None):
    """
    Intelligence Engine: Compares catalogs and identifies missing inventory gaps.
    """
    if not baseline_data:
        return "Please set a baseline website to enable comparison analysis."

    # 1. Map Baseline Products for fast lookup
    baseline_products = {p['name'].lower(): p for p in baseline_data.get('products', [])}
    
    report_sections = []
    report_sections.append(f"# Strategic Intelligence Report\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    report_sections.append(f"## 🏠 Baseline: {baseline_data.get('name', 'Your Site')}")
    report_sections.append(f"Tracking {len(baseline_products)} core products for comparison.\n")

    for comp in competitors_data:
        comp_name = comp.get('name', 'Competitor')
        comp_products = comp.get('products', [])
        
        matched_analysis = []
        missing_from_baseline = []
        
        for p in comp_products:
            name_lower = p['name'].lower()
            if name_lower in baseline_products:
                # PRICE COMPARISON
                b_price = baseline_products[name_lower].get('raw_price', 0)
                c_price = p.get('raw_price', 0)
                
                diff = ""
                if b_price and c_price:
                    p_diff = ((c_price - b_price) / b_price) * 100
                    diff = f"({'+' if p_diff > 0 else ''}{p_diff:.1f}% vs you)"
                
                matched_analysis.append(f"- **{p['name']}**: Competing at {p['price']} {diff}")
            else:
                # MISSING ITEM IDENTIFIED
                missing_from_baseline.append(f"- **{p['name']}** found at {p['price']}")

        # Build Section
        report_sections.append(f"### 🎯 Analysis: {comp_name}")
        
        if matched_analysis:
            report_sections.append("**Price Tracking (Matched Products):**")
            report_sections.extend(matched_analysis[:10]) # Top 10 matches
        
        if missing_from_baseline:
            report_sections.append("\n**🚀 Inventory Gaps (Items they have that you don't):**")
            report_sections.extend(missing_from_baseline[:15]) # Top 15 opportunities
            
        report_sections.append("\n" + "-"*30 + "\n")

    # Final Recommendation Logic
    report_sections.append("## 💡 Strategic Recommendations")
    if len(competitors_data) > 0:
        report_sections.append("1. **Inventory Expansion**: Review the 'Inventory Gaps' sections above to identify high-demand items missing from your catalog.")
        report_sections.append("2. **Pricing Optimization**: Adjust prices for matched products where competitors are significantly (>5%) cheaper.")
    
    return "\n".join(report_sections)