import os
import json
from datetime import datetime


class HistoryEngine:

    HISTORY_DIR = "intelligence_data/history"

    # -------------------------------------------
    def save_today(self, payload):

        os.makedirs(self.HISTORY_DIR, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")

        path = f"{self.HISTORY_DIR}/{today}.json"

        with open(path, "w") as f:
            json.dump(payload, f, indent=2)

        print(f"💾 Snapshot saved: {path}")

    # -------------------------------------------
    def load_yesterday(self):

        if not os.path.exists(self.HISTORY_DIR):
            return None

        files = sorted(os.listdir(self.HISTORY_DIR))

        if len(files) < 1:
            return None

        latest = files[-1]

        path = f"{self.HISTORY_DIR}/{latest}"

        with open(path) as f:
            return json.load(f)
