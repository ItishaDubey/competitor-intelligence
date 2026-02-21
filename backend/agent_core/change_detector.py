class ChangeDetector:

    # ---------------------------------------------------
    def detect(self, today_payload, yesterday_payload):

        if not yesterday_payload:
            return {}

        results = {}

        for comp in today_payload["competitors"]:

            cname = comp["name"]

            today_products = comp["products"]

            yesterday_products = self._get_competitor(
                cname,
                yesterday_payload
            )

            change_summary = self._compare_products(
                today_products,
                yesterday_products
            )

            results[cname] = change_summary

        return results

    # ---------------------------------------------------
    def _get_competitor(self, name, payload):

        for c in payload.get("competitors", []):
            if c["name"] == name:
                return c.get("products", [])

        return []

    # ---------------------------------------------------
    def _compare_products(self, today, yesterday):

        # ⭐ SWITCH TO SIGNATURE BASED KEYS
        today_map = {
            (p.get("signature"), p.get("variant_value")): p
            for p in today
        }

        y_map = {
            (p.get("signature"), p.get("variant_value")): p
            for p in yesterday
        }

        new_skus = []
        deleted_skus = []
        price_drops = []
        variant_expansion = []

        # ---------------- NEW SKUs ----------------
        for k, p in today_map.items():
            if k not in y_map:
                new_skus.append(p.get("name"))

        # ---------------- DELETED SKUs ----------------
        for k, p in y_map.items():
            if k not in today_map:
                deleted_skus.append(p.get("name"))

        # ---------------- PRICE CHANGES ----------------
        for k, p in today_map.items():

            if k in y_map:

                old_price = y_map[k].get("price")
                new_price = p.get("price")

                try:
                    if old_price and new_price:
                        if float(new_price) < float(old_price):
                            price_drops.append(p.get("name"))
                except:
                    pass

        # ---------------- VARIANT EXPANSION ----------------
        today_variants = {}
        y_variants = {}

        for p in today:
            today_variants.setdefault(
                p.get("signature"),
                set()
            ).add(p.get("variant_value"))

        for p in yesterday:
            y_variants.setdefault(
                p.get("signature"),
                set()
            ).add(p.get("variant_value"))

        for sig in today_variants:
            if sig in y_variants:
                if len(today_variants[sig]) > len(y_variants[sig]):
                    variant_expansion.append(sig)

        return {
            "new_skus": new_skus,
            "deleted_skus": deleted_skus,
            "price_drops": price_drops,
            "variant_expansion": variant_expansion
        }
