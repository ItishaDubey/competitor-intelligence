import json
import os

HISTORY_PATH = "memory/history.json"


class HistoryEngine:

    def load(self):
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH) as f:
                return json.load(f)
        return {}

    def save(self, data):
        os.makedirs("memory", exist_ok=True)
        with open(HISTORY_PATH, "w") as f:
            json.dump(data, f, indent=2)

    def detect_changes(self, competitor_name, current_products):

        history = self.load()
        previous = history.get(competitor_name, [])

        prev_names = {p["normalized_name"] for p in previous}
        curr_names = {p["normalized_name"] for p in current_products}

        new_products = [p for p in current_products if p["normalized_name"] not in prev_names]
        deleted_products = [p for p in previous if p["normalized_name"] not in curr_names]

        history[competitor_name] = current_products
        self.save(history)

        return new_products, deleted_products
