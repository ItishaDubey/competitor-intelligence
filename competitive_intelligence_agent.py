"""
Bulletproof Competitive Intelligence Agent
Actually finds products and handles errors properly
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import hashlib
import time
import re
import os
from urllib.parse import urljoin

class BulletproofCompetitiveAgent:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.data_dir = 'intelligence_data'
        self.ensure_data_dir()
        self.baseline = self.config.get('baseline')
        
        self.junk_keywords = [
            'about', 'terms', 'privacy', 'legal', 'cookie',
            'contact', 'support', 'faq', 'career', 'press'
        ]
        
    def load_config(self, config_file):
        if os.path.exists(config_file):
            with open(config_file) as f:
                return json.load(f)
        return {"baseline": None, "competitors": []}
    
    def ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def clean_soup(self, soup):
        """Remove junk"""
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'nav', 'header', 'footer']):
            tag.decompose()
        return soup
    
    def extract_prices(self, text):
        """Extract prices"""
        prices = []
        # Match patterns like "3% off", "7.27% off", etc
        discount_pattern = r'([\d.]+)%\s*[Oo]ff'
        
        # Also standard prices
        price_patterns = [
            r'\$(\d+(?:\.\d{2})?)',
            r'₹(\d+)',
            r'Rs\.?\s*(\d+)',
        ]
        
        for pattern in price_patterns:
            for match in re.findall(pattern, text):
                try:
                    price = float(match)
                    if 0.1 <= price <= 999999:
                        prices.append(price)
                except:
                    pass
        
        return sorted(list(set(prices)))
    
    def extract_products_aggressive(self, soup, url):
        """AGGRESSIVE product finding - will find K-Store products!"""
        products = []
        
        print(f"    🔍 Strategy 1: Looking for ANY cards/items...")
        
        # Find ALL divs that could be product cards
        all_divs = soup.find_all('div', recursive=True)
        
        potential_products = []
        
        for div in all_divs:
            # Skip if it's too big (likely container)
            if len(str(div)) > 5000:
                continue
            
            # Look for text content
            text_content = div.get_text(strip=True)
            
            # Skip if too short or too long
            if not text_content or len(text_content) < 5 or len(text_content) > 500:
                continue
            
            # Skip if it's likely junk
            if any(kw in text_content.lower() for kw in self.junk_keywords):
                continue
            
            # Look for product indicators
            has_image = div.find('img') is not None
            has_link = div.find('a') is not None
            has_price_indicator = bool(re.search(r'%\s*[Oo]ff|\$|\₹|Rs', text_content))
            
            # If it looks like a product
            if (has_image or has_link) and len(text_content) < 200:
                # Extract title (first significant text)
                title = None
                for tag in div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'span', 'p', 'div']):
                    t = tag.get_text(strip=True)
                    if t and 5 < len(t) < 100 and not any(kw in t.lower() for kw in self.junk_keywords):
                        title = t
                        break
                
                if not title:
                    # Use first line of text
                    lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                    if lines:
                        title = lines[0]
                
                if title and 3 < len(title) < 150:
                    potential_products.append({
                        'name': title,
                        'discount': self._extract_discount(text_content),
                        'price': self._extract_price(text_content),
                        'raw_text': text_content[:200]
                    })
        
        # Deduplicate by name
        seen_names = set()
        for p in potential_products:
            name = p['name']
            if name not in seen_names and len(name) > 3:
                seen_names.add(name)
                products.append(p)
        
        print(f"    ✓ Found {len(products)} potential products")
        
        # If we found products, return them
        if products:
            return products[:30]
        
        # Strategy 2: Look for links as products
        print(f"    🔍 Strategy 2: Analyzing links...")
        links = soup.find_all('a', href=True)[:50]
        
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            
            if not text or len(text) < 5 or len(text) > 100:
                continue
            
            if any(kw in text.lower() or kw in href.lower() for kw in self.junk_keywords):
                continue
            
            products.append({
                'name': text,
                'price': None,
                'url': href
            })
        
        return products[:30]
    
    def _extract_discount(self, text):
        """Extract discount percentage"""
        match = re.search(r'([\d.]+)%\s*[Oo]ff', text)
        if match:
            return f"{match.group(1)}% off"
        return None
    
    def _extract_price(self, text):
        """Extract price from text"""
        patterns = [r'\$(\d+(?:\.\d{2})?)', r'₹(\d+)', r'Rs\.?\s*(\d+)']
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return f"${match.group(1)}"
        return None
    
    def analyze_page(self, url, track_options):
        """Analyze page"""
        try:
            print(f"  📄 {url}")
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            soup = self.clean_soup(soup)
            
            analysis = {
                'url': url,
                'checked_at': datetime.now().isoformat(),
                'products': []
            }
            
            # Extract products
            if 'products' in track_options or 'content' in track_options:
                products = self.extract_products_aggressive(soup, url)
                analysis['products'] = products
                
                if products:
                    print(f"    ✅ Total: {len(products)} products found!")
                else:
                    print(f"    ⚠️  No products found")
            
            # Extract prices
            if 'pricing' in track_options or 'prices' in track_options:
                text = soup.get_text()
                prices = self.extract_prices(text)
                if prices:
                    analysis['price_range'] = {
                        'min': min(prices),
                        'max': max(prices),
                        'avg': round(sum(prices) / len(prices), 2),
                        'count': len(prices)
                    }
                    print(f"    💰 Price range: ${min(prices):.2f} - ${max(prices):.2f}")
            
            return analysis
            
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            return None
    
    def compare_data(self, current, previous):
        """Compare data - SAFE version that handles missing keys"""
        if not previous:
            return {'is_first_run': True}
        
        changes = {}
        
        # Safely get products
        curr_products = current.get('products', [])
        prev_products = previous.get('products', [])
        
        # Build dicts - handle both 'name' and 'title' keys
        curr_dict = {}
        for p in curr_products:
            name = p.get('name') or p.get('title') or str(p)
            if isinstance(name, str):
                curr_dict[name] = p
        
        prev_dict = {}
        for p in prev_products:
            name = p.get('name') or p.get('title') or str(p)
            if isinstance(name, str):
                prev_dict[name] = p
        
        # Find changes
        added = [name for name in curr_dict if name not in prev_dict]
        removed = [name for name in prev_dict if name not in curr_dict]
        
        if added:
            changes['new_products'] = added[:10]
        if removed:
            changes['removed_products'] = removed[:10]
        
        # Price range changes
        if 'price_range' in current and 'price_range' in previous:
            curr_avg = current['price_range']['avg']
            prev_avg = previous['price_range']['avg']
            diff_pct = ((curr_avg - prev_avg) / prev_avg) * 100
            
            if abs(diff_pct) > 5:
                changes['avg_price_change'] = {
                    'old_avg': prev_avg,
                    'new_avg': curr_avg,
                    'change_pct': round(diff_pct, 1)
                }
        
        return changes if changes else None
    
    def save_and_compare(self, company, page_name, data):
        """Save and compare - SAFE version"""
        if not data:
            return None
        
        safe = f"{company}_{page_name}".replace(' ','_').replace('/','_')
        file = f"{self.data_dir}/{safe}_history.json"
        
        history = []
        if os.path.exists(file):
            try:
                with open(file) as f:
                    history = json.load(f)
            except:
                history = []
        
        # Compare
        changes = None
        if history:
            try:
                changes = self.compare_data(data, history[-1])
            except Exception as e:
                print(f"    ⚠️  Comparison error: {e}")
                changes = None
        
        # Save
        history.append(data)
        with open(file, 'w') as f:
            json.dump(history[-10:], f, indent=2)
        
        return changes
    
    def compare_competitors(self, baseline_data, competitor_data, comp_name):
        """Compare with baseline"""
        insights = []
        
        if not baseline_data or not competitor_data:
            return insights
        
        base_count = len(baseline_data.get('products', []))
        comp_count = len(competitor_data.get('products', []))
        
        if base_count > 0 and comp_count > 0:
            if comp_count > base_count * 1.3:
                insights.append({
                    'type': 'product_range',
                    'priority': 'medium',
                    'message': f"{comp_name} offers {comp_count} products vs your {base_count}",
                    'recommendation': 'Consider expanding product range'
                })
        
        base_prices = baseline_data.get('price_range')
        comp_prices = competitor_data.get('price_range')
        
        if base_prices and comp_prices:
            base_avg = base_prices['avg']
            comp_avg = comp_prices['avg']
            diff_pct = ((comp_avg - base_avg) / base_avg) * 100
            
            if abs(diff_pct) > 10:
                insights.append({
                    'type': 'pricing',
                    'priority': 'high' if abs(diff_pct) > 20 else 'medium',
                    'message': f"{comp_name} avg price is {diff_pct:+.1f}% vs yours",
                    'recommendation': 'Review pricing' if diff_pct < 0 else 'Maintain pricing'
                })
        
        return insights
    
    def monitor_all(self):
        """Monitor all"""
        print("🔍 Monitoring Started\n")
        
        results = []
        baseline_data = None
        
        if self.baseline:
            print(f"📊 Baseline: {self.baseline['name']}")
            for page in self.baseline.get('pages_to_monitor', []):
                data = self.analyze_page(page['url'], page.get('track', ['products']))
                if data:
                    changes = self.save_and_compare(self.baseline['name'], page['name'], data)
                    baseline_data = data
                    
                    result = {
                        'company': self.baseline['name'],
                        'is_baseline': True,
                        'url': page['url'],
                        'products_found': len(data.get('products', [])),
                        'price_range': data.get('price_range')
                    }
                    
                    if changes and not changes.get('is_first_run'):
                        result['changes'] = changes
                    
                    if data.get('products'):
                        result['sample_products'] = data['products'][:5]
                    
                    results.append(result)
                time.sleep(2)
        
        for comp in self.config.get('competitors', []):
            print(f"\n🎯 Competitor: {comp['name']}")
            
            for page in comp.get('pages_to_monitor', []):
                data = self.analyze_page(page['url'], page.get('track', ['products']))
                if data:
                    changes = self.save_and_compare(comp['name'], page['name'], data)
                    
                    result = {
                        'company': comp['name'],
                        'is_baseline': False,
                        'url': page['url'],
                        'products_found': len(data.get('products', [])),
                        'price_range': data.get('price_range')
                    }
                    
                    if changes and not changes.get('is_first_run'):
                        result['changes'] = changes
                    
                    if baseline_data:
                        insights = self.compare_competitors(baseline_data, data, comp['name'])
                        if insights:
                            result['insights'] = insights
                    
                    if data.get('products'):
                        result['sample_products'] = data['products'][:5]
                    
                    results.append(result)
                time.sleep(3)
        
        return results
    
    def generate_digest(self, results):
        """Generate digest"""
        total_products = sum(r.get('products_found', 0) for r in results)
        has_changes = sum(1 for r in results if r.get('changes'))
        has_insights = sum(1 for r in results if r.get('insights'))
        
        return {
            'report_date': datetime.now().isoformat(),
            'summary': {
                'companies_monitored': len(results),
                'total_products_tracked': total_products,
                'changes_detected': has_changes,
                'insights_generated': has_insights
            },
            'detailed_results': results
        }
    
    def save_digest(self, digest):
        """Save digest"""
        file = f"{self.data_dir}/digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(file, 'w') as f:
            json.dump(digest, f, indent=2)
        print(f"\n✅ Saved: {file}")
        return file
    
    def run(self):
        """Run"""
        print("=" * 70)
        print("🤖 BULLETPROOF COMPETITIVE INTELLIGENCE")
        print("=" * 70)
        
        results = self.monitor_all()
        digest = self.generate_digest(results)
        self.save_digest(digest)
        
        print("\n📊 Generating report...")
        try:
            import subprocess, sys
            subprocess.run([sys.executable, 'generate_report.py'], check=True, capture_output=True)
            print("✅ Report ready")
        except:
            pass
        
        print("\n" + "=" * 70)
        print("✅ COMPLETE")
        print("=" * 70)
        print(f"Companies: {digest['summary']['companies_monitored']}")
        print(f"Products Found: {digest['summary']['total_products_tracked']}")
        print(f"Changes: {digest['summary']['changes_detected']}")
        print("=" * 70)
        
        return digest

if __name__ == "__main__":
    agent = BulletproofCompetitiveAgent()
    agent.run()