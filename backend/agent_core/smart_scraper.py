"""
SmartScraper v5 - Root cause fixes:

1. Woohoo: Hits their public API endpoints directly (not just the deals page DOM).
   Woohoo/PineLabs has a REST API at /api/... that returns full catalog JSON.
   We intercept ALL XHR responses and parse any that look like product catalogs.

2. Flipkart: More aggressive price extraction — reads the JSON API response
   from their search results page (they inject product data into __NEXT_DATA__
   or window.__INITIAL_STATE__) rather than relying on CSS class names.

3. KStore: Intercepts product JSON from their API + reads INR prices from DOM cards.

4. Prices ALWAYS stored as variant_value (even for competitor products),
   so the pricing matrix can show actual numbers.
"""

import re
import json
from urllib.parse import urlparse, urljoin

from playwright.sync_api import sync_playwright


# ─────────────────────────────────────────────────────────────
# KNOWN BRANDS (120+) — canonical sig → regex
# ─────────────────────────────────────────────────────────────
KNOWN_BRANDS = [
    # Gaming
    ("google_play",       r"\bgoogle\s*play\b"),
    ("steam",             r"\bsteam\b(?!\s*lysto)"),
    ("steam_lysto",       r"\bsteam\s*lysto\b|\blysto\b"),
    ("xbox",              r"\bxbox\b"),
    ("playstation",       r"\bplaystation\b|\bpsn\b"),
    ("nintendo",          r"\bnintendo\b"),
    ("minecraft",         r"\bminecraft\b"),
    ("roblox",            r"\broblox\b"),
    ("pubg",              r"\bpubg\b|\bbattlegrounds\b"),
    ("valorant",          r"\bvalorant\b"),
    ("freefire",          r"\bfree\s*fire\b"),
    ("garena",            r"\bgarena\b"),
    ("riot",              r"\briot\s*(games?|valorant|league)?\b"),
    ("league_of_legends", r"\bleague\s*of\s*legends\b"),
    # Streaming
    ("netflix",           r"\bnetflix\b"),
    ("spotify",           r"\bspotify\b"),
    ("hotstar",           r"\bhotstar\b|\bdisney\+?\b|\bdisney\s*plus\b"),
    ("zee5",              r"\bzee\s*5\b|\bzee5\b"),
    ("sonyliv",           r"\bsony\s*liv\b|\bsonyliv\b"),
    ("bookmyshow",        r"\bbook\s*my\s*show\b|\bbms\b"),
    ("primevideo",        r"\bamazon\s*prime\b|\bprime\s*video\b"),
    # E-commerce
    ("amazon_pay",        r"\bamazon\s*pay\b"),
    ("amazon",            r"\bamazon\b"),
    ("flipkart",          r"\bflipkart\b"),
    ("myntra",            r"\bmyntra\b"),
    ("nykaa",             r"\bnykaa\b"),
    ("ajio",              r"\bajio\b"),
    ("tatacliq",          r"\btata\s*cliq\b|\btatacliq\b"),
    ("croma",             r"\bcroma\b"),
    ("meesho",            r"\bmeesho\b"),
    ("reliance",          r"\breliance\b"),
    # Grocery
    ("zomato",            r"\bzomato\b"),
    ("swiggy",            r"\bswiggy\b"),
    ("bigbasket",         r"\bbigbasket\b"),
    ("natures_basket",    r"\bnature.{0,2}s?\s*basket\b"),
    ("blinkit",           r"\bblinkit\b"),
    ("zepto",             r"\bzepto\b"),
    # Restaurants
    ("dominos",           r"\bdomino.{0,2}s?\b"),
    ("pizzahut",          r"\bpizza\s*hut\b"),
    ("mcdonalds",         r"\bmcdonald.{0,2}s?\b"),
    ("kfc",               r"\bkfc\b"),
    ("subway",            r"\bsubway\b"),
    ("starbucks",         r"\bstarbucks\b"),
    ("chaayos",           r"\bchaayos\b"),
    ("burger_king",       r"\bburger\s*king\b"),
    ("barbeque_nation",   r"\bbarbeque\s*nation\b"),
    # Travel
    ("makemytrip",        r"\bmake\s*my\s*trip\b|\bmmt\b"),
    ("cleartrip",         r"\bcleartrip\b"),
    ("yatra",             r"\byatra\b"),
    ("ola",               r"\bola\s*(cabs?|rides?|money)?\b"),
    ("uber",              r"\buber\b"),
    ("oyo",               r"\boyo\b"),
    ("airbnb",            r"\bairbnb\b"),
    ("irctc",             r"\birctc\b"),
    ("air_india",         r"\bair\s*india\b"),
    ("indigo",            r"\bindigo\s*airline\b"),
    ("spicejet",          r"\bspicejet\b"),
    ("thomas_cook",       r"\bthomas\s*cook\b"),
    ("marriott",          r"\bmarriott\b"),
    ("taj",               r"\btaj\s*(experiences?|hotels?|group)?\b"),
    # Finance
    ("paytm",             r"\bpaytm\b"),
    ("phonepe",           r"\bphonepe\b"),
    ("gpay",              r"\bgoogle\s*pay\b|\bgpay\b"),
    ("cred",              r"\bcred\b"),
    ("mobikwik",          r"\bmobikwik\b"),
    ("pineperks",         r"\bpineperks\b"),
    # Telecom
    ("jio",               r"\bjio\b"),
    ("airtel",            r"\bairtel\b"),
    ("vi",                r"\bvodafone\b|\bvi\s+(recharge|prepaid|postpaid|store)\b"),
    ("bsnl",              r"\bbsnl\b"),
    # Dating
    ("tinder",            r"\btinder\b"),
    ("bumble",            r"\bbumble\b"),
    # Beauty/Fashion
    ("tira",              r"\btira\b"),
    ("purplle",           r"\bpurplle\b"),
    ("lifestyle",         r"\blifestyle\s*(store|retail|online)?\b"),
    ("shoppers_stop",     r"\bshoppers\s*stop\b"),
    ("pantaloons",        r"\bpantaloons\b"),
    ("westside",          r"\bwestside\b"),
    ("fabindia",          r"\bfabindia\b"),
    ("max_fashion",       r"\bmax\s*(fashion|retail|store|online)?\b"),
    ("globus",            r"\bglobus\b"),
    ("firstcry",          r"\bfirstcry\b"),
    ("allen_solly",       r"\ballen\s*solly\b"),
    ("van_heusen",        r"\bvan\s*heusen\b"),
    ("peter_england",     r"\bpeter\s*england\b"),
    ("easybuy",           r"\beasy\s*buy\b|\beasybuy\b"),
    ("home_centre",       r"\bhome\s*centre\b"),
    ("vijay_sales",       r"\bvijay\s*sales\b"),
    # Footwear/Sports
    ("bata",              r"\bbata\b"),
    ("puma",              r"\bpuma\b"),
    ("adidas",            r"\badidas\b"),
    ("nike",              r"\bnike\b"),
    ("reebok",            r"\breebok\b"),
    ("skechers",          r"\bskechers\b"),
    ("fastrack",          r"\bfastrack\b"),
    ("levi",              r"\blevi.{0,2}s?\b"),
    ("wildcraft",         r"\bwildcraft\b"),
    ("decathlon",         r"\bdecathlon\b"),
    ("mokobara",          r"\bmokobara\b"),
    # Jewellery
    ("tanishq",           r"\btanishq\b|\bmia\s*by\s*tanishq\b"),
    ("kalyan",            r"\bkalyan\b"),
    ("joyalukkas",        r"\bjoyalukkas\b"),
    ("jos_alukkas",       r"\bjos\s*alukkas\b"),
    ("grt",               r"\bgrt\b"),
    ("pcj",               r"\bpcj\b|\bp\.?c\.?\s*chandra\b"),
    ("giva",              r"\bgiva\b"),
    ("bhima",             r"\bbhima\b"),
    ("tbz",               r"\btbz\b"),
    ("ketan",             r"\bketan\b"),
    ("mia",               r"\bmia\s*by\b"),
    # Books/Education
    ("crossword",         r"\bcrossword\b"),
    ("luxe",              r"\bluxe\b"),
    # Gaming platforms
    ("unipin",            r"\bunipin\b"),
    # Healthcare
    ("netmeds",           r"\bnetmeds\b"),
    ("1mg",               r"\b1mg\b"),
    ("apollo",            r"\bapollo\b"),
    # Electronics
    ("boat",              r"\bboat\b"),
    ("xiaomi",            r"\bxiaomi\b|\bmi\s*store\b"),
    ("samsung",           r"\bsamsung\b"),
    ("apple",             r"\bapple\b"),
]

_NOISE_RE = re.compile(
    r"^(why|snack|fuel|discover|explore|shop now|get |check|find |how |what |the best|"
    r"top |new arrivals|featured|popular|trending|recommended|best )\b"
    r"|\b(login|sign in|sign up|register|faq|privacy|terms|contact)\b"
    r"|\b(footer|header|filter|sort by|relevance)\b"
    r"|\b(showing.*results|results for|customer rating)\b"
    r"|\b(captcha|scroll|click here|load more)\b"
    r"|\b(hot deals|best sellers|latest chart|all categories|all brands)\b"
    r"|\b(facebook|instagram|twitter|youtube|telegram|whatsapp)\b"
    r"|\b(app store|play store|download app)\b"
    r"|\b(woohoo special|current trend|web_widget)\b",
    re.IGNORECASE
)


def _is_noise(name: str) -> bool:
    if not name or len(name.strip()) < 3:
        return True
    return bool(_NOISE_RE.search(name.strip()))


def _get_signature(name: str):
    if not name:
        return None
    text = name.lower()
    for sig, pattern in KNOWN_BRANDS:
        if re.search(pattern, text):
            return sig
    return None


def _fallback_signature(name: str) -> str:
    text = name.lower()
    text = re.sub(
        r"\b(e-?gift|gift card|gift voucher|voucher|recharge|digital|instant|"
        r"online|india|buy|price|card|code|prepaid|egift|ncmc|gold|jewel|jewellery|"
        r"diamond|restaurant|grocery|offline|clothing|subscription|fashion|hd|month|"
        r"instant voucher|rs\.|inr)\b",
        " ", text
    )
    text = re.sub(r"[₹$€£]\s*\d[\d,]*", " ", text)
    text = re.sub(r"\b\d[\d,]*\b", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    words = [w for w in text.split() if len(w) > 2]
    return "_".join(words[:3])[:40] or "unknown"


def _clean_price(raw) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        v = float(raw)
        return v if 10 <= v <= 500_000 else None
    s = re.sub(r"[^\d.]", "", str(raw))
    try:
        v = float(s) if s else None
        return v if v and 10 <= v <= 500_000 else None
    except ValueError:
        return None


def _extract_denominations(obj: dict) -> list[float]:
    denoms = []
    raw_list = (
        obj.get("denominations") or obj.get("variants") or
        obj.get("amounts") or obj.get("values") or
        obj.get("prices") or []
    )
    if isinstance(raw_list, list):
        for item in raw_list:
            if isinstance(item, dict):
                v = _clean_price(
                    item.get("price") or item.get("sellingPrice") or
                    item.get("value") or item.get("amount") or
                    item.get("faceValue") or item.get("mrp")
                )
            else:
                v = _clean_price(item)
            if v:
                denoms.append(v)
    if not denoms:
        v = _clean_price(
            obj.get("price") or obj.get("sellingPrice") or obj.get("amount") or
            obj.get("displayPrice") or obj.get("faceValue") or obj.get("denomination") or
            obj.get("mrp") or obj.get("value")
        )
        if v:
            denoms.append(v)
    return sorted(set(denoms))


def _make_rows(name: str, sig: str, obj: dict, base_url: str = None) -> list[dict]:
    denoms = _extract_denominations(obj)
    cat = obj.get("category") or obj.get("categoryName")
    url_val = (obj.get("url") or obj.get("link") or
               obj.get("productUrl") or obj.get("deepLink") or obj.get("slug"))
    if url_val and base_url and not url_val.startswith("http"):
        url_val = urljoin(base_url, url_val)

    if denoms:
        return [
            {"name": name, "price": d, "variant_value": d,
             "category": cat, "url": url_val, "signature": sig}
            for d in denoms
        ]
    return [{"name": name, "price": None, "variant_value": None,
             "category": cat, "url": url_val, "signature": sig}]


def _walk_payload(data, strict_brands: bool = True, base_url: str = None) -> list[dict]:
    results = []

    def walk(obj, depth=0):
        if depth > 12:
            return
        if isinstance(obj, list):
            for item in obj:
                walk(item, depth + 1)
        elif isinstance(obj, dict):
            name = (
                obj.get("name") or obj.get("title") or obj.get("productName") or
                obj.get("displayName") or obj.get("voucherName") or
                obj.get("brandName") or obj.get("brand_name") or
                obj.get("product_name")
            )
            if name and isinstance(name, str) and not _is_noise(name):
                sig = _get_signature(name)
                if sig or not strict_brands:
                    if not sig:
                        sig = _fallback_signature(name)
                    rows = _make_rows(name, sig, obj, base_url)
                    results.extend(rows)
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    walk(v, depth + 1)

    walk(data)
    return results


# ─────────────────────────────────────────────────────────────
# KSTORE PARSER
# ─────────────────────────────────────────────────────────────

class _KStoreParser:
    """
    KStore intercepts XHR JSON. Their product cards show 'INR 403 | 4.23% Off'
    which we also parse from the DOM as fallback.
    """

    def extract(self, page, url: str) -> list[dict]:
        captured = []
        base_url = "https://" + urlparse(url).netloc

        def on_response(response):
            ct = response.headers.get("content-type", "")
            if "json" not in ct:
                return
            try:
                data = response.json()
                txt = json.dumps(data).lower()
                keywords = ("voucher", "denomination", "giftcard", "product",
                            "brand", "facevalue", "inr", "recharge", "egift")
                if any(k in txt for k in keywords):
                    captured.append(data)
            except Exception:
                pass

        page.on("response", on_response)
        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(5_000)

        results = []
        for payload in captured:
            results.extend(_walk_payload(payload, strict_brands=True, base_url=base_url))

        if not results:
            results = self._dom_fallback(page, url)

        return results

    def _dom_fallback(self, page, base_url: str) -> list[dict]:
        results = []
        seen = set()
        try:
            cards = page.locator(
                "[class*=product], [class*=card], [class*=voucher], "
                "[class*=item], a[href*='product'], a[href*='voucher']"
            ).all()
            for card in cards[:300]:
                try:
                    # Name
                    name = ""
                    for sel in ["h2", "h3", "h4", "h5", "p.title",
                                "[class*=name]", "[class*=title]", "p"]:
                        el = card.locator(sel).first
                        if el.count() > 0:
                            t = el.inner_text().strip()
                            if t and not _is_noise(t) and len(t) > 3:
                                name = t
                                break
                    if not name:
                        img = card.locator("img").first
                        if img.count() > 0:
                            name = img.get_attribute("alt") or ""

                    if not name or _is_noise(name) or name in seen:
                        continue
                    sig = _get_signature(name)
                    if not sig:
                        continue
                    seen.add(name)

                    # Price — KStore shows "INR 403" or "₹403"
                    price = None
                    full_text = card.inner_text()
                    for m in re.finditer(r"(?:INR|₹)\s*([\d,]+(?:\.\d+)?)", full_text, re.IGNORECASE):
                        v = _clean_price(m.group(1))
                        if v:
                            price = v
                            break

                    href = card.get_attribute("href") or ""
                    url_val = urljoin(base_url, href) if href else None

                    results.append({
                        "name": name, "price": price, "variant_value": price,
                        "category": None, "url": url_val, "signature": sig,
                    })
                except Exception:
                    continue
        except Exception:
            pass
        return results


# ─────────────────────────────────────────────────────────────
# WOOHOO PARSER
# ─────────────────────────────────────────────────────────────

class _WoohooParser:
    """
    Woohoo (PineLabs) - CONFIRMED API structure from diagnostic:

    API endpoint: https://www.woohoo.in/proxy/category/102?page=N
    Returns: {"api":"category","status":200,"data":{"_embedded":{"products":[...]}}}

    Each product has:
      - "name"            : product display name
      - "url_key"         : slug → https://www.woohoo.in/{url_key}
      - "min_custom_value": minimum price (string, e.g. "500")
      - "max_custom_value": maximum price (string, e.g. "5000")
      - "min_custom_price": alternate min price field
      - "max_custom_price": alternate max price field
      - "discounts"       : list of discount objects with discount.amount (%)

    Page 1 is in window.__INITIAL_STATE__ (inline script tag).
    Pages 2+ are XHR responses captured via page.on("response").

    Price strategy: Woohoo uses custom-range vouchers (buy ₹500–₹5000).
    We store min_custom_value as the representative price so the matrix
    shows "from ₹500" style comparison.
    """

    BASE_URL = "https://www.woohoo.in"

    # Woohoo category 102 = "More Brands - Gift Cards" (all brands page)
    CATEGORY_ID = 102
    # Page size is 30 products per page; we fetch up to 20 pages = 600 products
    MAX_PAGES = 20

    def extract(self, page, url: str) -> list[dict]:
        all_products = []
        pages_seen = set()

        # ── Step 1: Intercept XHR for pages loaded by scrolling ──
        def on_response(response):
            try:
                if f"woohoo.in/proxy/category/{self.CATEGORY_ID}" not in response.url:
                    return
                page_param = response.url.split("page=")[-1].split("&")[0]
                if page_param in pages_seen:
                    return
                pages_seen.add(page_param)
                data = response.json()
                products = (data.get("data", {})
                               .get("_embedded", {})
                               .get("products", []))
                if products:
                    print(f"    📦 Woohoo XHR page={page_param}: {len(products)} products")
                    all_products.extend(products)
            except Exception:
                pass

        page.on("response", on_response)

        # ── Step 2: Navigate and read page 1 from __INITIAL_STATE__ ──
        page.goto(url, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(3_000)
        self._read_initial_state(page, all_products, pages_seen)

        # ── Step 3: Scroll to trigger lazy-load of pages 2–N ──
        for _ in range(20):
            page.evaluate("window.scrollBy(0, window.innerHeight * 2)")
            page.wait_for_timeout(400)
        page.wait_for_timeout(2_000)

        # ── Step 4: Fetch any remaining pages directly via API ──
        # Woohoo's category API is public — no auth needed.
        # We use page.evaluate() to make fetch() calls from inside the browser
        # (same origin, so cookies/headers are inherited automatically).
        already = {int(p) for p in pages_seen if p.isdigit()}
        last_seen = max(already) if already else 1
        for page_num in range(1, self.MAX_PAGES + 1):
            if page_num in already:
                continue
            try:
                api_url = f"https://www.woohoo.in/proxy/category/{self.CATEGORY_ID}?page={page_num}"
                result = page.evaluate(f"""
                    async () => {{
                        try {{
                            const r = await fetch("{api_url}", {{
                                headers: {{
                                    "Accept": "application/json",
                                    "X-Requested-With": "XMLHttpRequest"
                                }}
                            }});
                            return await r.json();
                        }} catch(e) {{ return null; }}
                    }}
                """)
                if not result:
                    break
                products = (result.get("data", {})
                                  .get("_embedded", {})
                                  .get("products", []))
                if not products:
                    print(f"    ✅ Woohoo: no more products after page {page_num-1}")
                    break
                print(f"    📦 Woohoo fetch page={page_num}: {len(products)} products")
                all_products.extend(products)
                already.add(page_num)
            except Exception as e:
                print(f"    ⚠️  Woohoo page {page_num} fetch failed: {e}")
                break

        print(f"    📊 Woohoo total: {len(all_products)} products across {len(already)} pages")

        # ── Convert to standard rows, filter empty ────────────
        rows = []
        for p in all_products:
            if p.get("name") or p.get("product_name"):
                row = self._to_row(p)
                if row:
                    rows.append(row)
        return rows

    def _read_initial_state(self, page, all_products: list, pages_seen: set):
        """Page 1 is embedded in window.__INITIAL_STATE__ in a <script> tag."""
        try:
            state_str = page.evaluate(r"""
                () => {
                    try {
                        if (window.__INITIAL_STATE__) {
                            return JSON.stringify(window.__INITIAL_STATE__);
                        }
                        for (const s of document.querySelectorAll('script')) {
                            const t = s.textContent || '';
                            const m = t.match(/window\.__INITIAL_STATE__\s*=\s*(\{[\s\S]+?\});?\s*$/m);
                            if (m) return m[1];
                            if (t.includes('__INITIAL_STATE') && t.includes('products')) {
                                const m2 = t.match(/=\s*(\{[\s\S]+\})/);
                                if (m2) return m2[1];
                            }
                        }
                    } catch(e) {}
                    return null;
                }
            """)
            if not state_str:
                return
            state = json.loads(state_str)
            # Navigate to products array: appReducer.category.data._embedded.products
            products = (
                state.get("appReducer", {})
                     .get("category", {})
                     .get("data", {})
                     .get("_embedded", {})
                     .get("products", [])
            )
            if products:
                pages_seen.add("1")
                print(f"    📦 Woohoo __INITIAL_STATE__ (page 1): {len(products)} products")
                all_products.extend(products)
        except Exception as e:
            print(f"    ⚠️  __INITIAL_STATE__ read failed: {e}")

    def _to_row(self, p: dict) -> dict:
        """Convert a Woohoo product API object to our standard row format."""
        name = p.get("name") or p.get("product_name") or ""
        if not name or _is_noise(name):
            return {}

        sig = _get_signature(name) or _fallback_signature(name)

        # Price: use min_custom_value as the representative price
        # (Woohoo vouchers are open-range, e.g. ₹500–₹5000)
        price = _clean_price(
            p.get("min_custom_value") or p.get("min_custom_price")
        )

        # URL from url_key slug
        url_key = (
            p.get("url_key") or
            (p.get("_links", {}).get("url", {}) or {}).get("href", "")
        )
        url_val = f"{self.BASE_URL}/{url_key}" if url_key else None

        # Category from category_ids is just numbers — use a generic label
        cat = "gift_card"

        return {
            "name": name,
            "price": price,
            "variant_value": price,
            "category": cat,
            "url": url_val,
            "signature": sig,
            # Store price range for display
            "min_price": price,
            "max_price": _clean_price(
                p.get("max_custom_value") or p.get("max_custom_price")
            ),
            "discount_pct": (
                p.get("discounts", [{}])[0].get("discount", {}).get("amount")
                if p.get("discounts") else None
            ),
        }


# ─────────────────────────────────────────────────────────────
# FLIPKART PARSER
# ─────────────────────────────────────────────────────────────

class _FlipkartParser:
    """
    Flipkart gift card scraper.

    Diagnostic findings (search page):
      - XHR: only analytics, NO product data
      - JSON-LD: empty ([]  — search page doesn't populate it)
      - Prices: rendered client-side only, not in HTML

    Solution: Use Flipkart's CATEGORY page for gift cards instead of search.
    The category page URL is: https://www.flipkart.com/gift-cards/pr?sid=dih
    OR the specific gift card category: https://www.flipkart.com/gift-cards/buy-gift-cards-online/pr?sid=dih
    These pages have JSON-LD ItemList with names + URLs AND render prices in DOM.

    If the configured URL is a search URL, we redirect to the category URL.
    We also directly read any JSON-LD present and augment with DOM prices.
    """

    # Flipkart gift card category URLs that actually work
    CATEGORY_URLS = [
        "https://www.flipkart.com/gift-cards/pr?sid=dih",
        "https://www.flipkart.com/search?q=gift+cards&as=on&as-show=on&otracker=AS_Query_OrganicAutoSuggest_1_1_na_na_na&otracker1=AS_Query_OrganicAutoSuggest_1_1_na_na_na&as-pos=1&as-type=RECENT&suggestionId=gift+cards&requestId=&as-searchtext=gift+cards",
    ]

    # Current Flipkart price CSS selectors
    PRICE_SELS = [
        "._30jeq3", ".Nx9bqj", "._1_WHN1", "._3tbKJL", "._16Jk6d",
        "[class*='price']", "[class*='Price']", "._25b18c ._30jeq3",
        "div[class*='_30jeq3']", "span[class*='_30jeq3']",
    ]

    def extract(self, page, url: str) -> list[dict]:
        # If given search URL, try category URL first (more reliable)
        target_urls = []
        if "search?q=" in url or "otracker=search" in url:
            target_urls = self.CATEGORY_URLS + [url]
        else:
            target_urls = [url] + self.CATEGORY_URLS

        all_results = []
        for target_url in target_urls:
            try:
                results = self._scrape_url(page, target_url)
                if results:
                    print(f"    ✅ Flipkart got {len(results)} products from {target_url[:60]}")
                    all_results = results
                    break
            except Exception as e:
                print(f"    ⚠️  Flipkart URL failed ({target_url[:50]}): {e}")
                continue

        return all_results

    def _scrape_url(self, page, url: str) -> list[dict]:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(5_000)

        # Scroll to render all products
        for _ in range(6):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(600)
        page.wait_for_timeout(2_000)

        # Strategy 1: JSON-LD ItemList (names + URLs)
        ld_products = self._read_json_ld(page)
        print(f"    📋 Flipkart JSON-LD: {len(ld_products)} items")

        # Strategy 2: DOM prices — read all price elements in order
        dom_prices = self._read_dom_prices(page)
        print(f"    💰 Flipkart DOM prices found: {len(dom_prices)}")

        if ld_products:
            # Merge names from JSON-LD with prices from DOM by position
            results = []
            for i, p in enumerate(ld_products):
                price = dom_prices[i] if i < len(dom_prices) else None
                sig = _get_signature(p["name"]) or _fallback_signature(p["name"])
                results.append({
                    "name": p["name"],
                    "price": price,
                    "variant_value": price,
                    "min_price": price,
                    "max_price": None,
                    "discount_pct": None,
                    "category": "gift_card",
                    "url": p.get("url"),
                    "signature": sig,
                })
            return results

        # Strategy 3: Pure DOM fallback (product links + adjacent prices)
        return self._dom_fallback(page)

    def _read_json_ld(self, page) -> list[dict]:
        products = []
        try:
            scripts = page.evaluate("""
                () => Array.from(
                    document.querySelectorAll('script[type="application/ld+json"]')
                ).map(s => s.textContent || '')
            """)
            for text in (scripts or []):
                if not text.strip():
                    continue
                try:
                    data = json.loads(text)
                    # Handle array wrapper
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("@type") == "ItemList":
                                data = item
                                break
                        else:
                            continue
                    if data.get("@type") != "ItemList":
                        continue
                    for item in data.get("itemListElement", []):
                        # item can be {"@type":"ListItem","name":...,"url":...}
                        # or {"@type":"ListItem","item":{"name":...,"url":...}}
                        name = item.get("name") or (item.get("item") or {}).get("name", "")
                        url_val = item.get("url") or (item.get("item") or {}).get("url")
                        if name and not _is_noise(name):
                            products.append({
                                "name": name,
                                "url": url_val,
                                "position": item.get("position", len(products)),
                            })
                except Exception:
                    continue
        except Exception:
            pass
        return sorted(products, key=lambda x: x.get("position", 0))

    def _read_dom_prices(self, page) -> list[float | None]:
        """Read price elements from DOM in document order."""
        for sel in self.PRICE_SELS:
            try:
                elements = page.locator(sel).all()
                if len(elements) < 2:
                    continue
                prices = []
                for el in elements:
                    try:
                        text = el.inner_text().strip()
                        m = re.search(r"[₹₨]\s*([\d,]+(?:\.\d{1,2})?)", text)
                        if not m:
                            m = re.search(r"^[\d,]+$", text)
                        if m:
                            raw = m.group(1) if m.lastindex else m.group(0)
                            v = _clean_price(raw.replace(",", ""))
                            prices.append(v)
                    except Exception:
                        prices.append(None)
                if prices:
                    return prices
            except Exception:
                continue
        return []

    def _dom_fallback(self, page) -> list[dict]:
        results = []
        seen = set()
        try:
            links = page.locator("a[href*='/p/']").all()
            for link in links[:100]:
                try:
                    name = link.get_attribute("title") or ""
                    if not name:
                        name = link.inner_text().strip().split("\n")[0]
                    if not name or _is_noise(name) or name in seen:
                        continue
                    seen.add(name)

                    href = link.get_attribute("href") or ""
                    url_val = f"https://www.flipkart.com{href}" if href.startswith("/") else href

                    # Try to find price near this link
                    price = None
                    for anc in ["xpath=ancestor::li[1]", "xpath=ancestor::div[3]"]:
                        try:
                            c = link.locator(anc).first
                            if c.count() > 0:
                                for psel in self.PRICE_SELS:
                                    pel = c.locator(psel).first
                                    if pel.count() > 0:
                                        m = re.search(r"[₹₨]\s*([\d,]+)",
                                                      pel.inner_text())
                                        if m:
                                            price = _clean_price(
                                                m.group(1).replace(",", ""))
                                            break
                                if price:
                                    break
                        except Exception:
                            continue

                    results.append({
                        "name": name, "price": price, "variant_value": price,
                        "min_price": price, "max_price": None, "discount_pct": None,
                        "category": "gift_card", "url": url_val,
                        "signature": _get_signature(name) or _fallback_signature(name),
                    })
                except Exception:
                    continue
        except Exception:
            pass
        return results


# ─────────────────────────────────────────────────────────────
# MAIN SMART SCRAPER
# ─────────────────────────────────────────────────────────────

class SmartScraper:

    def _get_parser(self, url: str):
        domain = urlparse(url).netloc.lower()
        if "kstore" in domain:
            return _KStoreParser()
        if "woohoo" in domain:
            return _WoohooParser()
        if "flipkart" in domain:
            return _FlipkartParser()
        return _WoohooParser()

    def scrape(self, url: str) -> list[dict]:
        parser = self._get_parser(url)
        print(f"  🔍 Using parser: {parser.__class__.__name__} for {url}")

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 900},
                locale="en-IN",
                timezone_id="Asia/Kolkata",
            )
            page = context.new_page()

            try:
                raw = parser.extract(page, url)
            except Exception as e:
                print(f"  ⚠️  Parser error: {e}")
                raw = []
            finally:
                browser.close()

        seen = set()
        results = []
        for p in raw:
            name = (p.get("name") or "").strip()
            if not name or _is_noise(name):
                continue
            sig = p.get("signature") or _get_signature(name) or _fallback_signature(name)
            variant = p.get("variant_value")
            key = (sig, variant, name.lower()[:30])  # include name to avoid over-dedup
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "name": name,
                "price": p.get("price"),
                "variant_value": variant,
                "min_price": p.get("min_price") or p.get("price"),
                "max_price": p.get("max_price"),
                "discount_pct": p.get("discount_pct"),
                "category": p.get("category"),
                "url": p.get("url"),
                "signature": sig,
            })

        print(f"  ✅ Extracted {len(results)} clean products")
        return results