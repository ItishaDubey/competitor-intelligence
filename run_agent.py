"""
run_agent.py – standalone CLI runner for the CI agent.

Usage:
    python run_agent.py [--config CONFIG_PATH]

Defaults to test_config.json if no config is specified.
"""

import json
import sys
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="CI Agent – Competitive Intelligence Runner")
    parser.add_argument("--config", default="test_config.json", help="Path to config JSON file")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"❌ Config file not found: {args.config}")
        sys.exit(1)

    with open(args.config) as f:
        config = json.load(f)

    from backend.agent_core.orchestrator_v2 import CIAgentOrchestrator
    agent = CIAgentOrchestrator(config)
    digest = agent.run()

    print("\n📊 Summary:")
    print(f"  Baseline products: {len(digest.get('baseline', {}).get('products', []))}")
    for comp in digest.get("competitors", []):
        diff = comp.get("diff", {})
        print(f"  {comp['name']}: {len(comp['products'])} products, "
              f"{len(diff.get('missing', []))} gaps, "
              f"{len(diff.get('variant_gaps', []))} variant gaps")
    changes = digest.get("changes", {})
    print(f"  Changes vs yesterday: {changes.get('total', 0)}")

if __name__ == "__main__":
    main()