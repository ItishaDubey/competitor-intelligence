from backend.agent_core.navigator_v3 import Navigator
from backend.agent_core.extractor import Extractor
from backend.agent_core.baseline_engine import BaselineEngine
from backend.agent_core.matcher import Matcher
from backend.agent_core.intelligence_engine import IntelligenceEngine
from backend.agent_core.history_engine import HistoryEngine
from backend.reporting.generate_report import generate_report


class CIAgentOrchestrator:
    def __init__(self, config):
        self.config = config
        self.navigator = Navigator()
        self.extractor = Extractor()
        self.baseline_engine = BaselineEngine()
        self.matcher = Matcher()
        self.intelligence = IntelligenceEngine()
        self.history = HistoryEngine()

    def run(self):

        print("🔎 Loading baseline...")
        baseline_url = self.config["baseline"]["url"]

        baseline_products = self.baseline_engine.load_or_build(
            baseline_url,
            self.navigator,
            self.extractor
        )

        print(f"🏠 Baseline products loaded: {len(baseline_products)}")

        all_results = []

        print("🚀 Processing competitors...")

        # -----------------------------
        # PROCESS COMPETITORS
        # -----------------------------
        for competitor in self.config["competitors"]:
            print(f"➡️ Crawling: {competitor['name']}")

            site_map = self.navigator.discover(competitor["url"])
            competitor_products = self.extractor.extract(site_map)

            print(f"📦 {competitor['name']} products extracted: {len(competitor_products)}")

            diff = self.matcher.compare(
                baseline_products,
                competitor_products
            )

            insights = self.intelligence.generate(
                baseline_products,
                diff,
                competitor["name"]
            )

            # 🔥 Detect history changes
            new_products, deleted_products = self.history.detect_changes(
                competitor["name"],
                competitor_products
            )

            all_results.append({
                "competitor": competitor["name"],
                "diff": diff,
                "insights": insights,
                "raw_products": competitor_products,
                "new_products": new_products,
                "deleted_products": deleted_products,
                "price_range": diff.get("price_range", {})
            })

        # -----------------------------
        # BUILD REPORT PAYLOAD
        # -----------------------------
        print("📊 Generating report...")

        digest_payload = {
            "baseline": {
                "name": self.config["baseline"]["name"],
                "products": baseline_products
            },
            "competitors": []
        }

        for r in all_results:

            products_to_show = r["diff"].get("matched", [])

            # fallback if baseline matching weak
            if not products_to_show:
                products_to_show = r.get("raw_products", [])

            digest_payload["competitors"].append({
                "name": r["competitor"],
                "products": products_to_show,
                "missing": r["diff"].get("missing", []),
                "new_products": r.get("new_products", []),
                "deleted_products": r.get("deleted_products", []),
                "price_range": r.get("price_range", {}),
                "insights": r.get("insights", "")
            })

        generate_report(digest_payload)

        print("✅ Report generation complete.")
