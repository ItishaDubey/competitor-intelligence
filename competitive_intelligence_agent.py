"""
Bulletproof Competitive Intelligence Agent
Improved product detection with scoring and detail fetching.
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
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
        
        # 1. EXPANDED JUNK KEYWORDS TO FILTER NAV ITEMS
        self.junk_keywords = [
            'about', 'terms', 'privacy', 'legal', 'cookie',
            'contact', 'support', 'faq', 'career', 'press',
            'home', 'login', 'sign in', 'sign up', 'register',
            'cart', 'checkout', 'account', 'profile', 'menu',
            'search', 'subscribe', 'newsletter', 'follow us'
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
        """Remove technical junk but keep layout structure"""
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg']):
            tag.decompose()
        return soup
    
    def extract_prices(self, text):
        """Extract prices from generic text"""
        prices = []
        price_patterns = [
            r'\$\s?(\d+(?:\.\d{2})?)',
            r'₹\s?(\d+(?:,\d{3})*)',
            r'Rs\.?\s*(\d+(?:,\d{3})*)',
            r'€\s?(\d+(?:\.\d{2})?)',
            r'£\s?(\d+(?:\.\d{2})?)'
        ]
        
        for pattern in price_patterns:
            for match in re.findall(pattern, text):
                try:
                    # Clean the string (remove commas) and convert to float
                    clean_match = match.replace(',', '')
                    price = float(clean_match)
                    # Filter out likely years (2025) or tiny numbers
                    if 0.5 <= price <= 50000 and price != 2024 and price != 2025:
                        prices.append(price)
                except:
                    pass
        
        return sorted(list(set(prices)))

    def _score_element(self, text, has_price, has_img, has_link):
        """
        2. SCORING SYSTEM to differentiate Products from Nav Items
        """
        score = 0
        text_lower = text.lower()
        
        # Immediate disqualifiers
        if any(kw in text_lower for kw in self.junk_keywords):
            return -100
        if len(text) < 10: # Too short (e.g. "Home")
            return -10
            
        # Positive signals
        if has_price:
            score += 50  # Strongest signal
        if has_img:
            score += 10
        if has_link:
            score += 10
        
        # Context signals
        if "add to cart" in text_lower or "buy" in text_lower or "add" in text_lower:
            score += 20
        if "% off" in text_lower or "discount" in text_lower:
            score += 15
            
        return score

    def extract_products_aggressive(self, soup, base_url):
        """
        Improved Strategy: 
        1. Find container elements (likely product cards).
        2. Score them.
        3. Optional: Visit link to get details.
        """
        products = []
        print(f"    🔍 Scanning for product cards...")
        
        # Get all potential containers
        # We look for divs, lis, and articles which are common card containers
        cards = soup.find_all(['div', 'li', 'article'], recursive=True)
        
        candidates = []
        
        for card in cards:
            # Optimization: Skip massive containers (likely the whole page wrapper)
            if len(str(card)) > 10000: 
                continue

            text_content = card.get_text(" ", strip=True)
            if not text_content: continue

            # Check contents
            prices = self.extract_prices(text_content)
            has_price = len(prices) > 0
            has_img = card.find('img') is not None
            link_tag = card.find('a', href=True)
            has_link = link_tag is not None
            
            # Calculate score
            score = self._score_element(text_content, has_price, has_img, has_link)
            
            # Threshold: Needs a price OR a very high score (e.g. image + title + 'add to cart')
            if score > 30:
                # Extract Title
                title = None
                # Try specific heading tags first
                for tag in card.find_all(['h2', 'h3', 'h4', 'h5', 'strong', 'span']):
                    t = tag.get_text(strip=True)
                    if len(t) > 5 and len(t) < 100 and not any(k in t.lower() for k in self.junk_keywords):
                        title = t
                        break
                
                if not title:
                    title = text_content[:50] # Fallback

                # Get Link
                product_url = None
                if link_tag:
                    product_url = urljoin(base_url, link_tag['href'])

                candidates.append({
                    'name': title,
                    'price': f"${prices[0]}" if prices else "Check Details",
                    'raw_price': prices[0] if prices else 0,
                    'url': product_url,
                    'score': score
                })

        # Deduplicate and sort by score
        seen = set()
        final_products = []
        # Sort candidates by score descending
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        for p in candidates:
            if p['name'] not in seen:
                seen.add(p['name'])
                
                # 3. OPEN PRODUCT CARD (Optional - fetches details)
                # Only do this for high-confidence items to save time
                if p['url'] and 'http' in p['url'] and self.config.get('deep_scan', False):
                    details = self._fetch_product_details(p['url'])
                    if details:
                        p.update(details)
                
                final_products.append(p)
                if len(final_products) >= 20: # Limit to top 20 to avoid clutter
                    break
                    
        return final_products

    def _fetch_product_details(self, url):
        """Visits the specific product page to get more info"""
        try:
            # Add a small delay to be polite
            time.sleep(0.5) 
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            if resp.status_code == 200:
                s = BeautifulSoup(resp.content, 'html.parser')
                # Try to find a longer description
                desc = s.find('meta', {'name': 'description'})
                return {'description': desc['content'] if desc else 'No description'}
        except:
            return None
        return None

    def analyze_page(self, url, track_options):
        try:
            print(f"  📄 Analyzing: {url}")
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # 4. Remove nav/header/footer tags explicitly before processing
            for tag in soup.find_all(['nav', 'header', 'footer']):
                tag.decompose()
            
            soup = self.clean_soup(soup)
            
            analysis = {
                'url': url,
                'checked_at': datetime.now().isoformat(),
                'products': []
            }
            
            if 'products' in track_options or 'content' in track_options:
                products = self.extract_products_aggressive(soup, url)
                analysis['products'] = products
                print(f"    ✅ Found {len(products)} valid products")

            if 'pricing' in track_options or 'prices' in track_options:
                # Use the prices found in products for a more accurate range
                all_prices = [p['raw_price'] for p in analysis['products'] if p.get('raw_price')]
                
                # Fallback to text scan if no products found
                if not all_prices:
                    all_prices = self.extract_prices(soup.get_text())
                
                if all_prices:
                    analysis['price_range'] = {
                        'min': min(all_prices),
                        'max': max(all_prices),
                        'avg': round(sum(all_prices) / len(all_prices), 2),
                        'count': len(all_prices)
                    }
            
            return analysis
        except Exception as e:
            print(f"  ⚠️  Error analyzing {url}: {e}")
            return None

    # ... (Keep existing compare_data, save_and_compare, monitor_all, etc. from your original file) ...
    # The rest of the class methods (compare_data, monitor_all, run, etc.) 
    # from your original file are fine and don't need changes.
    
    def compare_data(self, current, previous):
        """Compare data - SAFE version that handles missing keys"""
        if not previous:
            return {'is_first_run': True}
        
        changes = {}
        curr_products = current.get('products', [])
        prev_products = previous.get('products', [])
        
        curr_names = {p.get('name') for p in curr_products if p.get('name')}
        prev_names = {p.get('name') for p in prev_products if p.get('name')}
        
        added = list(curr_names - prev_names)
        removed = list(prev_names - curr_names)
        
        if added:
            changes['new_products'] = added[:10]
        if removed:
            changes['removed_products'] = removed[:10]
        
        if 'price_range' in current and 'price_range' in previous:
            curr_avg = current['price_range']['avg']
            prev_avg = previous['price_range']['avg']
            # Avoid division by zero
            if prev_avg > 0:
                diff_pct = ((curr_avg - prev_avg) / prev_avg) * 100
                if abs(diff_pct) > 5:
                    changes['avg_price_change'] = {
                        'old_avg': prev_avg,
                        'new_avg': curr_avg,
                        'change_pct': round(diff_pct, 1)
                    }
        
        return changes if changes else None

    # ... Include the rest of your original methods (save_and_compare, monitor_all, generate_digest, save_digest, run) here ...
    # For brevity, assume the original logic for these methods is preserved.

    def run(self):
        # (Copy your original run method here)
        print("=" * 70)
        print("🤖 BULLETPROOF COMPETITIVE INTELLIGENCE v2")
        print("=" * 70)
        # ... logic ...
        pass

if __name__ == "__main__":
    # Ensure you copy the full class structure including monitor_all, etc.
    # If you paste this over your file, make sure to keep the helper methods!
    pass