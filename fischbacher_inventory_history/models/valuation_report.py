from datetime import date as python_date

from odoo import fields, models


class StockValuationReport(models.AbstractModel):
    _inherit = "stock_account.stock.valuation.report"

    def _get_report_data(
        self,
        date=False,
        product_category=False,
        warehouse=False,
    ):
        result = super()._get_report_data(
            date=date,
            product_category=product_category,
            warehouse=warehouse,
        )
        result["fischbacher_individual"] = self._fh_get_individual_data(date)
        return result

    def _fh_excluded_valuation_categories(self):
        return {
            920: "Maschinenmiete allgemein",
            923: "Maschinenmiete GEDA 300",
            928: "Maschinenmiete GEDA 200",
            930: "Maschinenmiete GEDA 500",
            925: "Maschinenmiete GEDA 1500",
            924: "Maschinenmiete GEDA 1200",
            926: "Maschinenmiete Schrägaufzug",
            927: "Maschinenmiete Schwenkaufzug",
            929: "Miete Transportachse GEDA/STE",
            931: "Zubehör Bauaufzug Geda/STE",
            945: "Mietkaufmaschinen",
            946: "Verkauf a.Anlagegeräte",
        }

    def _fh_normalize_category_name(self, name):
        return " ".join((name or "").split()).casefold()

    def _fh_without_excluded_valuation_categories(self, products):
        # Nur für Bereich 1 und Importlager 1 verwenden.
        # Importlager ML bleibt ungefiltert.
        #
        # Abgleich über bisherige Datenbank-IDs und exakte Namen.
        # Unterkategorien werden nicht automatisch ausgeschlossen.
        definitions = self._fh_excluded_valuation_categories()
        excluded_ids = set(definitions)
        excluded_names = set()

        for number, name in definitions.items():
            excluded_names.add(
                self._fh_normalize_category_name(name)
            )
            excluded_names.add(
                self._fh_normalize_category_name(
                    f"[{number}] {name}"
                )
            )

        categories = (
            products.mapped("categ_id")
            .sudo()
            .with_context(lang=False)
        )

        for category in categories:
            normalized_name = self._fh_normalize_category_name(
                category.name
            )

            if normalized_name in excluded_names:
                excluded_ids.add(category.id)

        return products.filtered(
            lambda product: (
                product.categ_id.id not in excluded_ids
            )
        )

    def _fh_empty(self, label, cutoff, mode):
        today_string = fields.Date.to_string(
            fields.Date.context_today(self)
        )

        return {
            "label": label,
            "date": fields.Date.to_string(cutoff),
            "mode": mode,
            "value": 0.0,
            "complete": True,
            "count": 0,
            "valued_count": 0,
            "zero_price_count": 0,
            "zero_cost_count": 0,
            "zero_cost_history_count": 0,
            "zero_cost_fallback_count": 0,
            "fallback_count": 0,
            "fallback_value": 0.0,
            "conflict_count": 0,
            "conflict_examples": [],
            "rows": [],
            "categories": [],
            "minimum_quantity": False,
            "adjusted_quantity_count": 0,
            "zero_stock_count": 0,
            "negative_stock_count": 0,
            "scope_counts": False,
            "rental_kind": False,

            # Originalbestand und Verfügbarkeit des Vergleichs.
            "original_stock_source": "",
            "original_stock_label": "Originalbestand",
            "original_stock_date": fields.Date.to_string(cutoff),
            "original_stock_warehouse": "",
            "original_stock_missing_count": 0,
            "original_stock_conflict_count": 0,
            "original_stock_assumed_zero_count": 0,
            "comparison_unavailable_count": 0,

            # Aktueller Odoo-Bestandsvergleich.
            "comparison_stock_source": "odoo_current",
            "comparison_stock_label": "Odoo-Bestand aktuell",
            "comparison_stock_date": today_string,

            # XML-Kompatibilitätsnamen.
            # Diese Felder enthalten aktuelle Odoo-Vergleichsdaten.
            "imported_stock_date": today_string,
            "imported_stock_warehouse": "",
            "imported_stock_difference_count": 0,
            "imported_stock_missing_count": 0,
            "imported_stock_conflict_count": 0,
        }

    def _fh_products(self, cutoff, stock_only=False):
        company = self.env.company

        Product = (
            self.env["product.product"]
            .sudo()
            .with_company(company)
            .with_context(
                skip_kit_qty_available=True,
                at_date=False,
                to_date=False,
                from_date=False,
            )
            ._with_valuation_context()
        )

        if cutoff != fields.Date.context_today(self):
            Product = Product.with_context(
                at_date=cutoff,
                to_date=cutoff,
            )

        domain = [("is_storable", "=", True)]

        if "company_id" in Product._fields:
            domain += [
                "|",
                ("company_id", "=", False),
                ("company_id", "=", company.id),
            ]

        if stock_only:
            domain += [("qty_available", "!=", 0)]

        return Product.with_context(active_test=False).search(
            domain,
            order="default_code, id",
        )

    def _fh_history(
        self,
        product_ids,
        cutoff,
        warehouse,
        start=None,
    ):
        if not product_ids:
            return {}

        self.env["product.inventory.history"].flush_model([
            "product_id",
            "date",
            "warehouse",
            "purchase_price",
            "quantity",
        ])

        # Preisregel:
        # Lager 1 vom 31.12.2025 oder jüngstes älteres Jahresende.
        #
        # Mit start wird diese Jahresendregel nicht angewendet.
        # Exakte Mengenabfragen und die historische
        # Dezemberauswertung bleiben dadurch unabhängig.
        annual_price_lookup = (
            warehouse == "1"
            and start is None
        )

        conditions = [
            "warehouse = %s",
            "date <= %s",
        ]

        params = [
            warehouse,
            (
                python_date(2025, 12, 31)
                if annual_price_lookup
                else cutoff
            ),
        ]

        if annual_price_lookup:
            conditions.extend([
                "EXTRACT(MONTH FROM date) = 12",
                "EXTRACT(DAY FROM date) = 31",
            ])

        if start is not None:
            conditions.append("date >= %s")
            params.append(start)

        conditions.append("product_id = ANY(%s)")
        params.append(product_ids)

        where_clause = " AND ".join(conditions)

        query = """
            WITH latest AS (
                SELECT product_id,
                       MAX(date) AS latest_date
                FROM product_inventory_history
                WHERE """ + where_clause + """
                GROUP BY product_id
            )
            SELECT h.product_id,
                   l.latest_date,
                   MIN(h.purchase_price),
                   MAX(h.purchase_price),
                   MIN(h.quantity),
                   MAX(h.quantity),
                   COUNT(*),
                   COUNT(h.purchase_price),
                   COUNT(h.quantity)
            FROM latest l
            JOIN product_inventory_history h
              ON h.product_id = l.product_id
             AND h.date = l.latest_date
            WHERE h.warehouse = %s
            GROUP BY h.product_id, l.latest_date
        """

        self.env.cr.execute(
            query,
            tuple(params + [warehouse]),
        )

        return {
            row[0]: row
            for row in self.env.cr.fetchall()
        }

    def _fh_original_import_stock(self, product_ids):
        # Mengenquelle für Bereich 1:
        # ausschließlich Lager 1, exakt 31.12.2025.
        import_date = python_date(2025, 12, 31)

        return self._fh_history(
            product_ids,
            import_date,
            "1",
            start=import_date,
        )

    def _fh_import_quantity(self, history):
        # Ohne Originalimport:
        # fiktive Menge 0 anzeigen, aber keinen Vergleich erlauben.
        # Der Status bleibt ausdrücklich "missing".
        if history is None:
            return 0.0, "missing"

        qty_min, qty_max = history[4:6]

        # Vorhandene, aber widersprüchliche oder unvollständige
        # Importmengen sind kein fehlender Import.
        # Solche Mengen dürfen nicht durch 0 ersetzt werden.
        if (
            qty_min is None
            or qty_max is None
            or history[6] != history[8]
            or abs(qty_max - qty_min) > 0.0000001
        ):
            return None, "conflict"

        # Eine tatsächlich importierte Menge 0 ist gültig
        # und wird regulär mit dem aktuellen Bestand verglichen.
        return qty_min, "ok"

    def _fh_conflict(self, data, product):
        # Bewertungsrelevanter Preis-/Importkonflikt.
        data["conflict_count"] += 1
        data["complete"] = False

        if len(data["conflict_examples"]) < 10:
            data["conflict_examples"].append(
                product.display_name
            )

    def _fh_count_zero_cost(self, data, price, fallback=False):
        if not self.env.company.currency_id.is_zero(price):
            return

        data["zero_cost_count"] += 1

        if fallback:
            data["zero_cost_fallback_count"] += 1
        else:
            data["zero_cost_history_count"] += 1

    def _fh_row(
        self,
        product,
        qty,
        price,
        source,
        source_date=False,
        original_qty=None,
        original_status="ok",
    ):
        if original_status == "missing":
            # Fehlender Originalimport wird nur für die Anzeige
            # als fiktiver Nullbestand geführt.
            original_qty = 0.0
        elif original_status == "ok" and original_qty is None:
            # Ohne gesonderte Originalmenge entspricht sie
            # der Bewertungsmenge.
            original_qty = qty

        original_available = (
            original_status == "ok"
            and original_qty is not None
        )

        original_assumed_zero = (
            original_status == "missing"
            and original_qty == 0.0
        )

        category = product.categ_id

        return {
            "id": product.id,
            "name": product.display_name,
            "product_template_id": product.product_tmpl_id.id,
            "category_id": category.id,
            "category_name": (
                category.complete_name
                or category.display_name
                or "Ohne Produktkategorie"
            ),
            "quantity": qty,
            "original_quantity": original_qty,
            "original_stock_status": original_status,
            "original_stock_available": original_available,
            "original_stock_assumed_zero": original_assumed_zero,
            "quantity_adjusted": (
                original_available
                and qty != original_qty
            ),
            "negative_stock": (
                original_available
                and original_qty < 0
            ),
            "uom_id": product.uom_id.id,
            "uom": product.uom_id.display_name,
            "uom_rounding": product.uom_id.rounding,
            "price": price,
            "value": qty * price,
            "zero_cost": self.env.company.currency_id.is_zero(price),
            "source": source,
            "source_date": (
                fields.Date.to_string(source_date)
                if source_date
                else ""
            ),
            "rent_ok": bool(product.rent_ok),
            "recurring_invoice": bool(product.recurring_invoice),

            # Aktueller Odoo-Bestand und Vergleich.
            "odoo_quantity": None,
            "odoo_stock_status": "missing",
            "odoo_stock_differs": False,
            "odoo_stock_delta": None,

            # XML-Kompatibilitätsnamen.
            "imported_quantity": None,
            "imported_stock_status": "missing",
            "imported_stock_differs": False,
            "imported_stock_delta": None,
        }

    def _fh_add_current_odoo_stock(self, data):
        company = self.env.company
        today_string = fields.Date.to_string(
            fields.Date.context_today(self)
        )

        data["comparison_stock_source"] = "odoo_current"
        data["comparison_stock_label"] = "Odoo-Bestand aktuell"
        data["comparison_stock_date"] = today_string

        data["imported_stock_date"] = today_string
        data["imported_stock_warehouse"] = ""
        data["imported_stock_difference_count"] = 0
        data["imported_stock_missing_count"] = 0
        data["imported_stock_conflict_count"] = 0
        data["comparison_unavailable_count"] = 0

        goods_mode = (
            data["mode"] == "current"
            and not data["minimum_quantity"]
        )

        if goods_mode:
            # Bereich 1:
            # Dieselbe aktuelle Menge verwenden, die bereits
            # Grundlage der Wertberechnung war.
            current_quantities = {
                row["id"]: row["quantity"]
                for row in data["rows"]
            }
        else:
            product_ids = sorted({
                row["id"]
                for row in data["rows"]
            })

            CurrentProduct = (
                self.env["product.product"]
                .sudo()
                .with_company(company)
                .with_context(
                    active_test=False,
                    skip_kit_qty_available=True,
                    at_date=False,
                    to_date=False,
                    from_date=False,
                )
                ._with_valuation_context()
            )

            current_products = CurrentProduct.browse(
                product_ids
            ).exists()

            current_quantities = {
                product.id: product.qty_available
                for product in current_products
            }

        for row in data["rows"]:
            row.update({
                "odoo_quantity": None,
                "odoo_stock_status": "missing",
                "odoo_stock_differs": False,
                "odoo_stock_delta": None,
                "imported_quantity": None,
                "imported_stock_status": "missing",
                "imported_stock_differs": False,
                "imported_stock_delta": None,
            })

            if row["id"] not in current_quantities:
                data["imported_stock_missing_count"] += 1
                data["comparison_unavailable_count"] += 1
                continue

            current_qty = current_quantities[row["id"]]

            row.update({
                "odoo_quantity": current_qty,
                "odoo_stock_status": "ok",
                "imported_quantity": current_qty,
                "imported_stock_status": "ok",
            })

            # Kein Vergleich bei:
            # - fehlendem Originalimport mit fiktiver Menge 0;
            # - widersprüchlichem Originalimport.
            #
            # Insbesondere neue Produkte werden dadurch nicht
            # als Bestandsabweichung gegenüber 0 markiert.
            if not row["original_stock_available"]:
                data["comparison_unavailable_count"] += 1
                continue

            delta = row["original_quantity"] - current_qty

            # Nur absolute Abweichungen über 100 markieren.
            # Exakt +100 oder -100 bleibt unmarkiert.
            differs = abs(delta) > 100.0

            row.update({
                "odoo_stock_differs": differs,
                "odoo_stock_delta": delta,
                "imported_stock_differs": differs,
                "imported_stock_delta": delta,
            })

            data["imported_stock_difference_count"] += int(
                differs
            )

    def _fh_finish(self, data):
        self._fh_add_current_odoo_stock(data)

        currency = self.env.company.currency_id

        data["value"] = currency.round(data["value"])
        data["fallback_value"] = currency.round(
            data["fallback_value"]
        )

        # Diese Zähler beziehen sich auf bewertete Produktzeilen.
        data["original_stock_missing_count"] = sum(
            row["original_stock_status"] == "missing"
            for row in data["rows"]
        )
        data["original_stock_conflict_count"] = sum(
            row["original_stock_status"] == "conflict"
            for row in data["rows"]
        )
        data["original_stock_assumed_zero_count"] = sum(
            row["original_stock_assumed_zero"]
            for row in data["rows"]
        )

        categories = {}

        for row in data["rows"]:
            category = categories.setdefault(
                row["category_id"],
                {
                    "id": row["category_id"],
                    "name": row["category_name"],
                    "value": 0.0,
                    "product_count": 0,
                    "template_count": 0,
                    "negative_stock_count": 0,
                    "zero_cost_count": 0,
                    "adjusted_quantity_count": 0,
                    "original_stock_missing_count": 0,
                    "original_stock_conflict_count": 0,
                    "original_stock_assumed_zero_count": 0,
                    "comparison_unavailable_count": 0,

                    # XML-Kompatibilitätsnamen.
                    "imported_stock_difference_count": 0,
                    "imported_stock_missing_count": 0,
                    "imported_stock_conflict_count": 0,

                    "rows": [],
                    "_templates": set(),
                    "_uoms": {},
                },
            )

            category["value"] += row["value"]
            category["product_count"] += 1

            category["negative_stock_count"] += int(
                row["negative_stock"]
            )
            category["zero_cost_count"] += int(
                row["zero_cost"]
            )
            category["adjusted_quantity_count"] += int(
                row["quantity_adjusted"]
            )
            category["original_stock_missing_count"] += int(
                row["original_stock_status"] == "missing"
            )
            category["original_stock_conflict_count"] += int(
                row["original_stock_status"] == "conflict"
            )
            category["original_stock_assumed_zero_count"] += int(
                row["original_stock_assumed_zero"]
            )
            category["comparison_unavailable_count"] += int(
                not row["original_stock_available"]
                or row["odoo_stock_status"] != "ok"
            )
            category["imported_stock_difference_count"] += int(
                row["odoo_stock_differs"]
            )
            category["imported_stock_missing_count"] += int(
                row["odoo_stock_status"] == "missing"
            )

            category["_templates"].add(
                row["product_template_id"]
            )
            category["rows"].append(row)

            unit = category["_uoms"].setdefault(
                row["uom_id"],
                {
                    "id": row["uom_id"],
                    "name": row["uom"],
                    "quantity": 0.0,
                    "original_quantity": 0.0,
                    "original_complete": True,
                    "original_count": 0,
                    "original_assumed_zero_count": 0,
                    "original_conflict_count": 0,

                    # Aktuelle Odoo-Vergleichsmenge.
                    "imported_quantity": 0.0,
                    "imported_complete": True,
                    "imported_count": 0,
                },
            )

            unit["quantity"] += row["quantity"]

            if row["original_stock_available"]:
                unit["original_quantity"] += row["original_quantity"]
                unit["original_count"] += 1
            else:
                # Eine fiktive Menge 0 ist keine nachgewiesene
                # historische Originalmenge.
                unit["original_complete"] = False

                if row["original_stock_assumed_zero"]:
                    unit["original_assumed_zero_count"] += 1
                else:
                    unit["original_conflict_count"] += 1

            if row["odoo_stock_status"] == "ok":
                unit["imported_quantity"] += row["odoo_quantity"]
                unit["imported_count"] += 1
            else:
                unit["imported_complete"] = False

        for category in categories.values():
            category["value"] = currency.round(
                category["value"]
            )
            category["template_count"] = len(
                category.pop("_templates")
            )

            units = list(category.pop("_uoms").values())

            for unit in units:
                # Ausschließlich fiktive Nullbestände:
                # Summe 0 anzeigen, aber original_complete=False.
                #
                # Ohne echte Originalmengen und mit Konflikten:
                # keine verlässliche Originalsumme ausweisen.
                if (
                    not unit["original_count"]
                    and unit["original_conflict_count"]
                ):
                    unit["original_quantity"] = None

            category["quantity_by_uom"] = sorted(
                units,
                key=lambda unit: (
                    unit["name"].casefold(),
                    unit["id"],
                ),
            )

            category["mixed_uom"] = (
                len(category["quantity_by_uom"]) > 1
            )
            category["single_quantity"] = (
                category["quantity_by_uom"][0]["quantity"]
                if not category["mixed_uom"]
                else None
            )

            category["rows"].sort(
                key=lambda row: (
                    row["name"].casefold(),
                    row["id"],
                )
            )

        data["categories"] = sorted(
            categories.values(),
            key=lambda category: (
                category["name"].casefold(),
                category["id"],
            ),
        )

        return data

    def _fh_scope_counts(self, products):
        rent = products.filtered(
            lambda product: product.rent_ok
        )
        subscriptions = products.filtered(
            lambda product: product.recurring_invoice
        )
        both = rent & subscriptions

        rent_templates = rent.mapped("product_tmpl_id")
        subscription_templates = subscriptions.mapped(
            "product_tmpl_id"
        )

        return {
            "rent_variants": len(rent),
            "subscription_variants": len(subscriptions),
            "both_variants": len(both),
            "union_variants": len(products),
            "rent_templates": len(rent_templates),
            "subscription_templates": len(
                subscription_templates
            ),
            "both_templates": len(
                rent_templates & subscription_templates
            ),
            "union_templates": len(
                products.mapped("product_tmpl_id")
            ),
            "archived_variants": len(
                products.filtered(
                    lambda product: not product.active
                )
            ),
        }

    def _fh_current_valuation(
        self,
        label,
        cutoff,
        products,
        prices,
        minimum_quantity=False,
        rental_kind=False,
        original_stock=None,
    ):
        # Kategorieausschluss nur für Bereich 1.
        if not minimum_quantity:
            products = self._fh_without_excluded_valuation_categories(
                products
            )

        data = self._fh_empty(label, cutoff, "current")

        data["count"] = len(products)
        data["minimum_quantity"] = minimum_quantity
        data["rental_kind"] = rental_kind

        current_quantities = {}

        if minimum_quantity:
            # Mietbereiche behalten ihre bisherige Mengenquelle.
            data["original_stock_source"] = "odoo_at_date"
            data["original_stock_label"] = (
                "Originalbestand zum Berichtsdatum"
            )
            data["scope_counts"] = self._fh_scope_counts(
                products
            )
        else:
            data["original_stock_source"] = "import_exact"
            data["original_stock_label"] = (
                "Importbestand 31.12.2025 – Lager 1"
            )
            data["original_stock_date"] = "2025-12-31"
            data["original_stock_warehouse"] = "1"

            if original_stock is None:
                original_stock = self._fh_original_import_stock(
                    products.ids
                )

            # Bereich 1 wird ausschließlich mit aktuellen
            # Odoo-Mengen im bestehenden Bewertungskontext bewertet.
            current_products = products.with_context(
                at_date=False,
                to_date=False,
                from_date=False,
            )

            current_quantities = {
                product.id: product.qty_available
                for product in current_products
            }

        for product in products:
            history = prices.get(product.id)

            if minimum_quantity:
                # Mietbereiche:
                # Odoo-Stichtagsbestand, mindestens 1.
                original_qty = product.qty_available
                original_status = "ok"
                qty = max(original_qty, 1.0)
                minimum_adjusted = qty != original_qty
            else:
                # Bereich 1:
                # Originalmenge aus dem exakten Import.
                # Ohne Import: fiktive 0, kein Vergleich.
                original_qty, original_status = (
                    self._fh_import_quantity(
                        original_stock.get(product.id)
                    )
                )

                # Bewertung unabhängig vom Originalimport
                # ausschließlich mit aktuellem Odoo-Bestand.
                qty = current_quantities[product.id]
                minimum_adjusted = False

            # Nur nachgewiesene Originalmengen in diesen
            # Bestandszählern berücksichtigen.
            if original_status == "ok":
                data["zero_stock_count"] += int(
                    original_qty == 0
                )
                data["negative_stock_count"] += int(
                    original_qty < 0
                )

            data["adjusted_quantity_count"] += int(
                minimum_adjusted
            )

            if history is None:
                price = product.with_company(
                    self.env.company
                ).standard_price

                source = (
                    "standard_price "
                    "(aktuell; keine Jahresend-Quelle bis 31.12.2025)"
                )
                source_date = False

                data["fallback_count"] += 1
                data["fallback_value"] += qty * price
            else:
                minimum, maximum = history[2:4]

                if (
                    minimum is None
                    or maximum is None
                    or history[6] != history[7]
                    or abs(maximum - minimum) > 0.0000001
                ):
                    self._fh_conflict(data, product)
                    continue

                price = minimum
                source = (
                    "Historischer EK – Lager 1 "
                    "(Jahresend-Eintrag)"
                )
                source_date = history[1]

                data["zero_price_count"] += int(
                    price == 0.0
                )

            self._fh_count_zero_cost(
                data,
                price,
                fallback=history is None,
            )

            row = self._fh_row(
                product,
                qty,
                price,
                source,
                source_date,
                original_qty=original_qty,
                original_status=original_status,
            )

            # Nur Miet-Mindestmengenanpassungen kennzeichnen.
            row["quantity_adjusted"] = bool(
                minimum_adjusted
            )

            data["rows"].append(row)
            data["value"] += row["value"]
            data["valued_count"] += 1

        return self._fh_finish(data)

    def _fh_imported_valuation(self, warehouse, products):
        # Nur Importlager 1 filtern.
        # Importlager ML behält die genannten Kategorien.
        if warehouse == "1":
            products = self._fh_without_excluded_valuation_categories(
                products
            )

        start = python_date(2025, 12, 1)
        end = python_date(2025, 12, 31)

        data = self._fh_empty(
            "Importierter Bestand Dezember 2025 – Lager " + warehouse,
            end,
            "historical",
        )

        data["original_stock_source"] = "import_december"
        data["original_stock_label"] = (
            "Importierter Dezemberbestand – Lager " + warehouse
        )
        data["original_stock_warehouse"] = warehouse

        prices = self._fh_history(
            products.ids,
            end,
            warehouse,
            start=start,
        )

        candidates = products.filtered(
            lambda product: product.id in prices
        )
        data["count"] = len(candidates)

        for product in candidates:
            history = prices[product.id]
            price_min, price_max, qty_min, qty_max = history[2:6]

            if (
                any(value is None for value in history[2:6])
                or history[6] != history[7]
                or history[6] != history[8]
                or abs(price_max - price_min) > 0.0000001
                or abs(qty_max - qty_min) > 0.0000001
            ):
                self._fh_conflict(data, product)
                continue

            self._fh_count_zero_cost(
                data,
                price_min,
                fallback=False,
            )

            # Historische Importbewertung unverändert:
            # Menge und EK aus derselben neuesten
            # Dezemberzeile je Produkt und Importlager.
            row = self._fh_row(
                product,
                qty_min,
                price_min,
                "Importierter Bestand und EK – Lager " + warehouse,
                history[1],
            )

            data["rows"].append(row)
            data["value"] += row["value"]
            data["valued_count"] += 1
            data["zero_price_count"] += int(
                price_min == 0.0
            )

        return self._fh_finish(data)

    def _fh_get_individual_data(self, date):
        today = fields.Date.context_today(self)

        filter_date = (
            fields.Date.to_date(date)
            if date
            else today
        ) or today

        company = self.env.company

        data = {
            "date": fields.Date.to_string(filter_date),
            "filter_date": fields.Date.to_string(filter_date),
            "currency_ok": (
                company.currency_id == self.env.ref("base.EUR")
            ),
            "missing_fields": [],
            "current": [],
            "historical": [],
            "rental_overlap": {
                "variants": 0,
                "templates": 0,
            },
        }

        missing = [
            name
            for name in ("rent_ok", "recurring_invoice")
            if name not in self.env["product.product"]._fields
        ]
        data["missing_fields"] = missing

        if missing or not data["currency_ok"]:
            return data

        # Mietbereiche verwenden das ausgewählte Berichtsdatum.
        all_current = self._fh_products(filter_date)

        # Bereich 1:
        # Importdatum nur für Originalmenge und Vergleich.
        # Die Bewertung verwendet den aktuellen Odoo-Bestand.
        goods_date = python_date(2025, 12, 31)

        goods_candidates = self._fh_products(today).filtered(
            lambda product: (
                not product.rent_ok
                and not product.recurring_invoice
            )
        )

        goods_candidates = (
            self._fh_without_excluded_valuation_categories(
                goods_candidates
            )
        )

        original_stock = self._fh_original_import_stock(
            goods_candidates.ids
        )

        # Aktuelle Bestände auch ohne Originalimport aufnehmen.
        # Vorhandene Originalimporte bleiben bei aktuellem
        # Bestand 0 ebenfalls für die Anzeige berücksichtigt.
        goods = goods_candidates.filtered(
            lambda product: (
                product.qty_available != 0
                or product.id in original_stock
            )
        )

        short_term = all_current.filtered(
            lambda product: product.rent_ok
        )
        long_term = all_current.filtered(
            lambda product: product.recurring_invoice
        )

        price_product_ids = sorted(
            set(goods.ids)
            | set(short_term.ids)
            | set(long_term.ids)
        )

        # Preisregel unverändert:
        # 31.12.2025 oder jüngstes älteres Jahresende aus Lager 1.
        prices = self._fh_history(
            price_product_ids,
            filter_date,
            "1",
        )

        data["rental_overlap"] = {
            "variants": len(short_term & long_term),
            "templates": len(
                short_term.mapped("product_tmpl_id")
                & long_term.mapped("product_tmpl_id")
            ),
        }

        data["current"] = [
            self._fh_current_valuation(
                "1. Warenbestand – ohne Vermietungs-/Abonnement-Haken",
                goods_date,
                goods,
                prices,
                original_stock=original_stock,
            ),
            self._fh_current_valuation(
                "2a. Kurzzeitmiete - Kleingeräte-Mietpark",
                filter_date,
                short_term,
                prices,
                minimum_quantity=True,
                rental_kind="short_term",
            ),
            self._fh_current_valuation(
                "2b. Langzeitmiete - Geda Bauaufzüge",
                filter_date,
                long_term,
                prices,
                minimum_quantity=True,
                rental_kind="long_term",
            ),
        ]

        # Gemeinsame Produktauswahl ohne Kategorieausschluss.
        # Nur Importlager 1 wird innerhalb der Bewertung gefiltert.
        imported_products = self._fh_products(today)

        data["historical"] = [
            self._fh_imported_valuation(
                "1",
                imported_products,
            ),
            self._fh_imported_valuation(
                "ML",
                imported_products,
            ),
        ]

        return data


class InventoryHistoryValuationIndex(models.Model):
    _inherit = "product.inventory.history"

    def init(self):
        self.env.cr.execute(
            """
            CREATE INDEX IF NOT EXISTS fischbacher_history_price_date_idx
            ON product_inventory_history (product_id, date DESC)
            WHERE warehouse = '1'
            """
        )

        self.env.cr.execute(
            """
            CREATE INDEX IF NOT EXISTS fischbacher_history_ml_price_date_idx
            ON product_inventory_history (product_id, date DESC)
            WHERE warehouse = 'ML'
            """
        )
