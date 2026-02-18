"""
Deep-Dive Competitive Intelligence Agent
- Visits product pages to find hidden prices (CodaShop fix)
- Matches competitor products to YOUR baseline products
- Explicitly handles Baseline data
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import re
import os
from urllib.parse import urljoin
from difflib import SequenceMatcher

class DeepDiveAgent:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.data_dir = 'intelligence_data'
        self.ensure_data_dir()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
        self.junk_keywords = [
            'login', 'signin', 'account', 'cart', 'checkout', 'profile', 
            'contact', 'help', 'support', 'terms', 'privacy', 'career',
            'menu', 'navigation', 'search', 'language', 'currency', 'news'
        ]

    def load_config(self, config_file):
        if os.path.exists(config_file):
            with open(config_file) as f: return json.load(f)
        return {"competitors": []}

    def ensure_data_dir(self):
        if not os.path.exists(self.data_dir): os.makedirs(self.data_dir)

    def clean_soup(self, soup):
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg', 'header', 'footer', 'nav', 'aside']):
            tag.decompose()
        return soup

    def extract_price(self, text):
        """Robust price extractor"""
        if not text: return None
        # Handle $10, 10 USD, 10.00, etc.
        patterns = [
            r'\$\s?(\d+(?:\.\d{2})?)',
            r'(\d+(?:\.\d{2})?)\s?USD',
            r'₹\s?(\d+(?:,\d{3})*)',
            r'Rs\.?\s*(\d+(?:,\d{3})*)',
            r'€\s?(\d+(?:\.\d{2})?)'
        ]
        
        candidates = []
        for p in patterns:
            for match in re.findall(p, text):
                try:
                    val = float(match.replace(',', ''))
                    # Filter out years (2025) or tiny amounts
                    if 0.5 <= val <= 50000 and val not in [2024, 2025]:
                        candidates.append(val)
                except: continue
        
        return min(candidates) if candidates else None

    def _deep_scrape_product(self, product_url):
        """
        Visits the specific product page.
        CRITICAL for sites like CodaShop where price is only on the detail page.
        """
        try:
            time.sleep(0.5) # Be polite
            resp = self.session.get(product_url, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # 1. Look for Price in the detail page
            # Usually inside H1, H2, or specific price classes
            text = soup.get_text()
            price = self.extract_price(text)
            
            # 2. Look for specific metadata (OpenGraph)
            if not price:
                og_price = soup.find("meta", property="product:price:amount")
                if og_price: price = float(og_price["content"])

            return {'price': price}
        except:
            return {'price': None}

    def find_products(self, url):
        """Finds product cards and then DIVES into them"""
        print(f"  📄 Scanning: {url}")
        try:
            resp = self.session.get(url, timeout=15)
            soup = self.clean_soup(BeautifulSoup(resp.content, 'html.parser'))
            
            # 1. Identify Product Cards (Image + Link + Text)
            cards = soup.find_all(['div', 'article', 'li', 'a'])
            found_products = []
            seen_urls = set()
            
            for card in cards:
                if len(str(card)) > 5000: continue # Skip wrappers
                
                # Must have a link
                link = card.find('a', href=True) if card.name != 'a' else card
                if not link: continue
                
                href = link['href']
                full_url = urljoin(url, href)
                
                # Filter junk
                if full_url in seen_urls: continue
                if any(j in full_url.lower() for j in self.junk_keywords): continue
                if len(href) < 5: continue

                # Get Title
                title = card.get_text(" ", strip=True)
                if len(title) < 4 or len(title) > 200: continue
                
                # Heuristic: Valid products usually have an image OR a price
                has_img = card.find('img')
                initial_price = self.extract_price(title)
                
                # Scoring to accept as candidate
                is_candidate = False
                if initial_price: is_candidate = True
                elif has_img and len(title) < 50: is_candidate = True # Short title + Img = Likely Product
                
                if is_candidate:
                    seen_urls.add(full_url)
                    found_products.append({
                        'name': title[:60], # Truncate long titles
                        'url': full_url,
                        'price': initial_price
                    })

            # 2. DEEP DIVE: Visit top 15 candidates to confirm price
            # This fixes the CodaShop issue where price is missing on listing
            final_products = []
            print(f"    🔍 Deep scanning {min(len(found_products), 15)} items for details...")
            
            for prod in found_products[:15]:
                # If we already have a price, great. If not, visit the page.
                if not prod['price']:
                    details = self._deep_scrape_product(prod['url'])
                    if details and details['price']:
                        prod['price'] = details['price']
                
                # Only keep if we found a price OR it looks very valid
                if prod['price']:
                    final_products.append(prod)
                elif len(prod['name']) > 5: # Keep items without price if title looks good
                    final_products.append(prod)
            
            return final_products

        except Exception as e:
            print(f"    ❌ Error: {e}")
            return []

    def match_products(self, baseline_products, competitor_products):
        """Finds products in competitor list that match baseline products"""
        if not baseline_products: return
        
        for c_prod in competitor_products:
            best_match = None
            highest_ratio = 0.0
            
            for b_prod in baseline_products:
                # Fuzzy string matching
                ratio = SequenceMatcher(None, b_prod['name'].lower(), c_prod['name'].lower()).ratio()
                if ratio > 0.4: # 40% similarity threshold
                    if ratio > highest_ratio:
                        highest_ratio = ratio
                        best_match = b_prod
            
            if best_match:
                c_prod['match'] = {
                    'name': best_match['name'],
                    'price': best_match['price'],
                    'diff': 0
                }
                # Calculate price diff
                if c_prod['price'] and best_match['price']:
                    diff = ((c_prod['price'] - best_match['price']) / best_match['price']) * 100
                    c_prod['match']['diff'] = diff

    def run(self):
        print("="*60 + "\n🤖 DEEP DIVE INTELLIGENCE AGENT\n" + "="*60)
        
        full_report = {
            'report_date': datetime.now().isoformat(),
            'baseline': None,
            'competitors': []
        }

        # 1. Scrape Baseline First
        baseline_products = []
        if self.config.get('baseline'):
            b_conf = self.config['baseline']
            print(f"\n🏠 Analyzing Baseline: {b_conf['name']}")
            for page in b_conf['pages_to_monitor']:
                prods = self.find_products(page['url'])
                baseline_products.extend(prods)
            
            full_report['baseline'] = {
                'name': b_conf['name'],
                'products': baseline_products
            }
            print(f"    ✅ Found {len(baseline_products)} baseline products")

        # 2. Scrape Competitors
        for comp in self.config.get('competitors', []):
            print(f"\n🎯 Analyzing Competitor: {comp['name']}")
            comp_products = []
            for page in comp.get('pages_to_monitor', []):
                prods = self.find_products(page['url'])
                comp_products.extend(prods)
            
            # 3. Match with Baseline
            if baseline_products:
                self.match_products(baseline_products, comp_products)

            full_report['competitors'].append({
                'name': comp['name'],
                'products': comp_products
            })

        # Save
        f_name = f"{self.data_dir}/digest_latest.json"
        with open(f_name, 'w') as f: json.dump(full_report, f, indent=2)
        
        print("\n📊 Generating Report...")
        os.system("python generate_report.py")

if __name__ == "__main__":
    DeepDiveAgent().run()