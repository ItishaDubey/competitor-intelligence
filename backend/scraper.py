import asyncio
from playwright.async_api import async_playwright


async def scrape_url_smart(url: str):

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        )

        page = await context.new_page()

        try:
            print(f"🕵️ Agent Deep-Scanning: {url}")

            await page.goto(url, wait_until="networkidle", timeout=60000)

            products = await page.evaluate(
                """
                () => {

                    const noise = ["login","home","cart","account","help","sign in"];

                    const items = [];

                    const cards = document.querySelectorAll(
                        'div[class*="product"], div[class*="item"], article, .card'
                    );

                    cards.forEach(el => {

                        let nameEl = el.querySelector(
                            'h1,h2,h3,h4,[class*="title"],[class*="name"]'
                        );

                        if(!nameEl) return;

                        let name = nameEl.innerText?.trim();
                        if(!name) return;

                        if(noise.some(n => name.toLowerCase().includes(n))) return;

                        let priceNode = Array.from(
                            el.querySelectorAll("span,div,p,b,strong")
                        ).find(n => n.innerText.match(/[₹$]/));

                        let priceText = priceNode ? priceNode.innerText : null;

                        let raw = 0;
                        if(priceText){
                            raw = parseFloat(
                                priceText.replace(/[^0-9.]/g,'')
                            ) || 0;
                        }

                        items.push({
                            name:name,
                            price:priceText,
                            raw_price:raw
                        });
                    });

                    return items;
                }
                """
            )

            return {
                "url": url,
                "products": products or [],
                "product_count": len(products or [])
            }

        except Exception as e:
            print("⚠️ scrape_url_smart error:", e)
            return {"url": url, "products": [], "error": str(e)}

        finally:
            await browser.close()
