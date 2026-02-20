import json
from backend.agent_core.orchestrator import CIAgentOrchestrator

CONFIG_FILE = "test_config.json"

def main():
    print("🚀 Starting CI Agent V2...")

    with open(CONFIG_FILE) as f:
        config = json.load(f)

    agent = CIAgentOrchestrator(config)
    agent.run()

    print("✅ Agent run completed.")

if __name__ == "__main__":
    main()
