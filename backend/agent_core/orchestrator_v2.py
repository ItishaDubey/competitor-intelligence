"""
CIAgentOrchestrator – main entry point for the competitive intelligence agent.

Run flow:
  1. Scrape baseline products (smart scraper)
  2. Scrape each competitor's products
  3. Match/compare using ProductMatcher
  4. Generate insights (AI or rule-based)
  5. Detect changes vs yesterday
  6. Save snapshot + generate HTML report
"""

import os
import json
from datetime import datetime

from backend.agent_core.smart_scraper import SmartScraper
from backend.agent_core.matcher_v2 import ProductMatcher
from backend.agent_core.insight_engine import InsightEngine
from backend.agent_core.change_detector_v2 import ChangeDetectorV2
from backend.reporting.report_generator import generate_report


HISTORY_DIR = "intelligence_data/history"
LATEST_FILE = "intelligence_data/report_latest.json"
REPORT_PATH = "reports/competitive_report.html"


class CIAgentOrchestrator:

    def __init__(self, config: dict):
        self.config = config
        self.scraper = SmartScraper()
        self.matcher = ProductMatcher()
        self.insight_engine = InsightEngine()
        self.change_detector = ChangeDetectorV2()

    # ──────────────────────────────────────────────────────────
    # PUBLIC
    # ──────────────────────────────────────────────────────────

    def run(self) -> dict:
        print("\n🚀 CI Agent starting…\n")

        # ── 1. Baseline ──────────────────────────────────────
        baseline_cfg = self.config.get("baseline", {})
        print(f"📥 Scraping baseline: {baseline_cfg.get('name')}")
        baseline_products = self._scrape_source(baseline_cfg)
        print(f"   → {len(baseline_products)} baseline products loaded\n")

        # ── 2. Competitors ───────────────────────────────────
        competitor_results = []

        for comp_cfg in self.config.get("competitors", []):
            name = comp_cfg.get("name")
            print(f"🔍 Processing competitor: {name}")
            comp_products = self._scrape_source(comp_cfg)
            print(f"   → {len(comp_products)} products scraped")

            diff = self.matcher.match(baseline_products, comp_products)
            print(
                f"   → matched:{len(diff['matched'])}  "
                f"missing:{len(diff['missing'])}  "
                f"variant_gaps:{len(diff['variant_gaps'])}  "
                f"price_diffs:{len(diff['price_diffs'])}"
            )

            competitor_results.append({
                "name": name,
                "products": comp_products,
                "diff": diff,
                "insights": {},          # filled in after change detection
            })
            print()

        # ── 3. Load yesterday + detect changes ───────────────
        yesterday = self._load_yesterday()
        digest = {
            "generated_at": datetime.now().isoformat(),
            "baseline": {
                "name": baseline_cfg.get("name"),
                "products": baseline_products,
            },
            "competitors": competitor_results,
        }

        changes = self.change_detector.detect(digest, yesterday)
        digest["changes"] = changes

        if changes.get("total", 0):
            print(f"📈 {changes['total']} changes detected vs yesterday\n")
        else:
            print("✅ No changes vs yesterday\n")

        # ── 4. Generate insights ─────────────────────────────
        for comp in competitor_results:
            print(f"💡 Generating insights for {comp['name']}…")
            comp["insights"] = self.insight_engine.generate(
                baseline_name=baseline_cfg.get("name", "Baseline"),
                baseline_products=baseline_products,
                competitor_name=comp["name"],
                diff=comp["diff"],
                changes=changes.get("changes", []),
            )

        # ── 5. Persist ────────────────────────────────────────
        self._save_snapshot(digest)
        self._save_latest(digest)

        # ── 6. Report ─────────────────────────────────────────
        print("\n📄 Generating HTML report…")
        generate_report(digest, REPORT_PATH)

        print("\n✅ CI Agent run complete.\n")
        return digest

    # ──────────────────────────────────────────────────────────
    # PRIVATE
    # ──────────────────────────────────────────────────────────

    def _scrape_source(self, source_cfg: dict) -> list[dict]:
        """Scrape using the URL (and optional pages) in source_cfg."""
        url = source_cfg.get("url")
        pages = source_cfg.get("pages_to_monitor", [])

        if not url and pages:
            url = pages[0].get("url")

        if not url:
            print(f"  ⚠️  No URL for {source_cfg.get('name')}")
            return []

        try:
            return self.scraper.scrape(url)
        except Exception as e:
            print(f"  ❌ Scrape failed: {e}")
            return []

    def _load_yesterday(self) -> dict | None:
        if not os.path.exists(HISTORY_DIR):
            return None
        files = sorted(f for f in os.listdir(HISTORY_DIR) if f.endswith(".json"))
        if not files:
            return None
        path = os.path.join(HISTORY_DIR, files[-1])
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None

    def _save_snapshot(self, digest: dict):
        os.makedirs(HISTORY_DIR, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(HISTORY_DIR, f"{today}.json")
        with open(path, "w") as f:
            json.dump(digest, f, indent=2)
        print(f"💾 Snapshot saved → {path}")

    def _save_latest(self, digest: dict):
        os.makedirs(os.path.dirname(LATEST_FILE), exist_ok=True)
        with open(LATEST_FILE, "w") as f:
            json.dump(digest, f, indent=2)


# ── Standalone entry point ────────────────────────────────────

def main():
    config_path = os.environ.get("CONFIG_PATH", "test_config.json")
    with open(config_path) as f:
        config = json.load(f)
    agent = CIAgentOrchestrator(config)
    agent.run()


if __name__ == "__main__":
    main()