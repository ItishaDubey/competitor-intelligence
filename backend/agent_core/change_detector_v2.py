"""
ChangeDetectorV2 - detects changes between today and yesterday snapshots.

Fix for Woohoo: products with no price/variant are keyed by (signature, name)
so they still get tracked across runs. Previously all Woohoo products keyed to
(sig, None) which would collapse all rows of same brand into one key → hiding changes.
"""


class ChangeDetectorV2:

    def detect(self, today_payload: dict, yesterday_payload: dict | None) -> dict:
        if not yesterday_payload:
            return {"status": "first_run", "changes": []}

        changes = []

        today_comps = {c["name"]: c for c in today_payload.get("competitors", [])}
        yest_comps  = {c["name"]: c for c in yesterday_payload.get("competitors", [])}

        for name, today_comp in today_comps.items():
            yest_comp = yest_comps.get(name)
            comp_changes = self._compare(
                name,
                today_comp.get("products", []),
                yest_comp.get("products", []) if yest_comp else [],
            )
            changes.extend(comp_changes)

        # Baseline changes
        base_today = today_payload.get("baseline", {}).get("products", [])
        base_yest  = yesterday_payload.get("baseline", {}).get("products", [])
        if base_today and base_yest:
            changes.extend(self._compare(
                today_payload.get("baseline", {}).get("name", "Baseline"),
                base_today, base_yest
            ))

        return {
            "status": "changes_detected" if changes else "no_changes",
            "total": len(changes),
            "changes": changes,
        }

    def _make_key(self, p: dict) -> tuple:
        """
        Unique key per product row.
        If there's a variant_value, use (sig, variant_value).
        If no variant_value (Woohoo brand-only rows), use (sig, name) so
        each brand is tracked even without denomination data.
        """
        sig = p.get("signature") or "unknown"
        var = p.get("variant_value")
        if var is not None:
            return (sig, var)
        return (sig, (p.get("name") or "").lower().strip())

    def _compare(self, comp_name: str, today_products: list, yest_products: list) -> list:
        changes = []

        today_map = {self._make_key(p): p for p in today_products}
        yest_map  = {self._make_key(p): p for p in yest_products}

        # New SKUs
        for key, p in today_map.items():
            if key not in yest_map:
                changes.append({
                    "type": "new_sku",
                    "competitor": comp_name,
                    "product": p.get("name"),
                    "variant": p.get("variant_value"),
                    "price": p.get("price"),
                    "url": p.get("url"),
                })

        # Removed SKUs
        for key, p in yest_map.items():
            if key not in today_map:
                changes.append({
                    "type": "removed_sku",
                    "competitor": comp_name,
                    "product": p.get("name"),
                    "variant": p.get("variant_value"),
                    "old_price": p.get("price"),
                    "url": p.get("url"),
                })

        # Price changes
        for key in set(today_map) & set(yest_map):
            tp = today_map[key]
            yp = yest_map[key]
            t_p = tp.get("price")
            y_p = yp.get("price")
            if t_p and y_p:
                try:
                    t_f, y_f = float(t_p), float(y_p)
                    if abs(t_f - y_f) > 0.5:
                        pct = round((t_f - y_f) / y_f * 100, 1)
                        changes.append({
                            "type": "price_change",
                            "competitor": comp_name,
                            "product": tp.get("name"),
                            "variant": tp.get("variant_value"),
                            "old_price": y_p,
                            "new_price": t_p,
                            "pct_change": pct,
                            "direction": "up" if pct > 0 else "down",
                            "url": tp.get("url"),
                        })
                except (TypeError, ValueError):
                    pass

        return changes