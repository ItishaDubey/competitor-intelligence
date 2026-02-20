import json
import os

class BaselineEngine:
    MEMORY_FILE = "memory/baseline.json"

    def load_or_build(self, url, navigator, extractor):
        if os.path.exists(self.MEMORY_FILE):
            with open(self.MEMORY_FILE) as f:
                return json.load(f)

        site_map = navigator.discover(url)
        products = extractor.extract(site_map)

        with open(self.MEMORY_FILE, "w") as f:
            json.dump(products, f, indent=2)

        return products
