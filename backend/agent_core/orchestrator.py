from backend.agent_core.navigator_v3 import Navigator
from backend.agent_core.extractor import Extractor
from backend.agent_core.baseline_engine import BaselineEngine
from backend.agent_core.matcher import ProductMatcher
from backend.agent_core.intelligence_engine import IntelligenceEngine
from backend.agent_core.history_engine import HistoryEngine
from backend.agent_core.change_detector import ChangeDetector
from backend.reporting.generate_report import generate_report


class CIAgentOrchestrator:

    def __init__(self, config):

        self.config = config

        self.navigator = Navigator()
        self.extractor = Extractor()
        self.baseline_engine = BaselineEngine()

        # ⭐ CORRECT MATCHER
        self.matcher = ProductMatcher()

        self.intelligence = IntelligenceEngine()

        self.history = HistoryEngine()
        self.change_detector = ChangeDetector()

    # =====================================================
    # RUN AGENT
    # =====================================================
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

        # --------------------------------------------------
        # PROCESS COMPETITORS
        # --------------------------------------------------
        for competitor in self.config["competitors"]:

            print(f"➡️ Crawling: {competitor['name']}")

            site_map = self.navigator.discover(competitor["url"])
            competitor_products = self.extractor.extract(site_map)

            print(
                f"📦 {competitor['name']} products extracted: {len(competitor_products)}"
            )

            diff = self.matcher.match(
                baseline_products,
                competitor_products
            )

            insights = self.intelligence.generate(
                baseline_products,
                diff,
                competitor["name"]
            )

            all_results.append({
                "name": competitor["name"],
                "products": competitor_products,
                "diff": diff,
                "insights": insights
            })

        # --------------------------------------------------
        # BUILD REPORT PAYLOAD
        # --------------------------------------------------
        print("📊 Generating report...")

        digest_payload = {
            "baseline": {
                "name": self.config["baseline"]["name"],
                "products": baseline_products
            },
            "competitors": all_results
        }

        # ⭐ HISTORY + CHANGE DETECTION
        yesterday = self.history.load_yesterday()

        changes = self.change_detector.detect(
            digest_payload,
            yesterday
        )

        digest_payload["changes"] = changes

        self.history.save_today(digest_payload)

        generate_report(digest_payload)

        print("✅ Report generation complete.")
