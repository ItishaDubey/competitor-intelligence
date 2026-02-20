import json
import os
from datetime import datetime

# ---------------------------------------------------------
# CORE ENGINES
# ---------------------------------------------------------
from backend.agent_core.navigator_v3 import Navigator
from backend.agent_core.extractor import Extractor
from backend.agent_core.baseline_engine import BaselineEngine
from backend.agent_core.matcher import Matcher
from backend.agent_core.intelligence_engine import IntelligenceEngine

# ---------------------------------------------------------
# DATA PIPELINE ENGINES
# ---------------------------------------------------------
from backend.agent_core.product_ingestion_engine import ProductIngestionEngine
from backend.agent_core.product_normalizer import ProductNormalizer
from backend.agent_core.product_signature_engine import ProductSignatureEngine
from backend.agent_core.variant_engine import VariantEngine
from backend.agent_core.product_source_resolver import ProductSourceResolver

# ---------------------------------------------------------
# HISTORY + CHANGE DETECTION
# ---------------------------------------------------------
from backend.agent_core.history_engine import HistoryEngine
from backend.agent_core.change_detector import ChangeDetector

# ---------------------------------------------------------
# REPORTING
# ---------------------------------------------------------
from backend.reporting.generate_report import generate_report


# =========================================================
# ⭐ PRODUCTION ORCHESTRATOR — CIAgentV3
# =========================================================
class CIAgentV3:

    def __init__(self, config):

        self.config = config

        # -----------------------------
        # Core Engines
        # -----------------------------
        self.navigator = Navigator()
        self.extractor = Extractor()
        self.baseline_engine = BaselineEngine()
        self.matcher = Matcher()
        self.intelligence = IntelligenceEngine()

        # -----------------------------
        # Data Processing Engines
        # -----------------------------
        self.ingestion = ProductIngestionEngine()
        self.normalizer = ProductNormalizer()
        self.variant_engine = VariantEngine()
        self.source_resolver = ProductSourceResolver()

        # -----------------------------
        # Memory + Change Detection
        # -----------------------------
        self.history = HistoryEngine()
        self.change_detector = ChangeDetector()

    # =====================================================
    # UNIVERSAL PRODUCT FETCHER
    # =====================================================
    def fetch_products(self, source):

        print(f"\n📡 Fetching products for {source['name']}")

        raw_products = []

        # -------------------------------------------------
        # 1️⃣ Explicit API ingestion
        # -------------------------------------------------
        if source.get("api"):
            try:
                raw_products = self.ingestion.fetch(source)
                print("✅ API ingestion success")
            except Exception as e:
                print(f"⚠️ API failed: {e}")

        # -------------------------------------------------
        # 2️⃣ Smart API Discovery
        # -------------------------------------------------
        if not raw_products:
            try:
                api_payloads = self.source_resolver.detect_api_products(
                    source["url"]
                )

                if api_payloads:
                    raw_products = self.ingestion.parse_api_payloads(
                        api_payloads
                    )
                    print("🔥 Smart API discovery used")

            except Exception as e:
                print(f"⚠️ Smart API detection failed: {e}")

        # -------------------------------------------------
        # 3️⃣ Navigator + Extractor Fallback
        # -------------------------------------------------
        if not raw_products:

            print("⚠️ No API products found — crawl disabled for stability")

            try:
                site_map = self.navigator.discover(source["url"])
                raw_products = self.extractor.extract(site_map)
            except Exception as e:
                print(f"❌ Navigator failed: {e}")

        # -------------------------------------------------
        # Normalize Products
        # -------------------------------------------------
        normalized = self.normalizer.normalize(raw_products)

        print(f"📦 Normalized products: {len(normalized)}")

        return normalized

    # =====================================================
    # RUN FULL AGENT
    # =====================================================
    def run(self):

        print("\n🚀 Starting CI Agent V3...\n")

        # =================================================
        # STEP 1 — BASELINE INGESTION
        # =================================================
        baseline_source = self.config["baseline"]

        baseline_products = self.fetch_products(baseline_source)

        print(f"\n🏠 Baseline products loaded: {len(baseline_products)}")

        all_results = []

        # =================================================
        # STEP 2 — PROCESS COMPETITORS
        # =================================================
        for competitor in self.config["competitors"]:

            print(f"\n➡️ Processing competitor: {competitor['name']}")

            competitor_products = self.fetch_products(competitor)

            # -------------------------------------------------
            # Variant + Pricing Intelligence
            # -------------------------------------------------
            diff = self.variant_engine.compare(
                baseline_products,
                competitor_products
            )

            # -------------------------------------------------
            # Strategic AI Insights
            # -------------------------------------------------
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

        # =================================================
        # STEP 3 — BUILD REPORT PAYLOAD
        # =================================================
        digest_payload = {
            "generated_at": datetime.now().isoformat(),
            "baseline": {
                "name": baseline_source["name"],
                "products": baseline_products
            },
            "competitors": all_results
        }

        # =================================================
        # STEP 4 — MEMORY + CHANGE DETECTION
        # =================================================
        try:
            yesterday = self.history.load_yesterday()

            changes = self.change_detector.detect(
                digest_payload,
                yesterday
            )

            digest_payload["changes"] = changes

        except Exception as e:
            print(f"⚠️ Change detection skipped: {e}")

        # =================================================
        # STEP 5 — SAVE DATA FOR DASHBOARD
        # =================================================
        os.makedirs("intelligence_data", exist_ok=True)

        with open("intelligence_data/report_latest.json", "w") as f:
            json.dump(digest_payload, f, indent=2)

        # Save history snapshot
        try:
            self.history.save_today(digest_payload)
        except Exception as e:
            print(f"⚠️ History save failed: {e}")

        # =================================================
        # STEP 6 — GENERATE REPORT UI
        # =================================================
        print("\n📊 Generating report UI...")
        generate_report(digest_payload)

        print("\n✅ CI Agent V3 completed successfully.\n")


# =========================================================
# ENTRYPOINT
# =========================================================
def main():

    with open("test_config.json") as f:
        config = json.load(f)

    agent = CIAgentV3(config)
    agent.run()


if __name__ == "__main__":
    main()
