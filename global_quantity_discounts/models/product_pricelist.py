# Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import fields, models
from odoo.tools import float_compare

#: Verhindert Rekursion, wenn Regeln auf anderen Preislisten basieren.
SKIP_GLOBAL_QUANTITY_KEY = "skip_global_quantity_pricelist"


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    is_global_quantity_pricelist = fields.Boolean(
        string="Global berücksichtigen",
        copy=False,
        help=(
            "Alle Regeln dieser Preisliste (auch Kategorie- und globale "
            "Regeln) werden zusätzlich zur Preisliste jedes Angebots bzw. "
            "Auftrags geprüft, z. B. 'Default' und 'Mengenstaffeln (EUR)'. "
            "Kundenspezifische Preislisten nicht markieren – ihre Preise "
            "gelten nur für Kunden mit dieser Preisliste. Der niedrigste "
            "Preis gewinnt."
        ),
    )

    # ------------------------------------------------------------------
    # Kandidaten
    # ------------------------------------------------------------------

    def _get_global_quantity_pricelists(self, currency):
        """Global zu berücksichtigende Preislisten (ohne `self`).

        Nur Preislisten derselben Währung: Festpreise rechnet Odoo nicht
        zwischen Währungen um.
        """
        company = self.company_id or self.env.company
        return self.env["product.pricelist"].search([
            ("is_global_quantity_pricelist", "=", True),
            ("company_id", "in", [False, company.id]),
            ("currency_id", "=", currency.id),
            ("id", "not in", self.ids),
        ], order="id")

    # ------------------------------------------------------------------
    # Preisberechnung
    # ------------------------------------------------------------------

    def _compute_price_rule(
        self, products, quantity, *, currency=None, uom=None, date=False,
        compute_price=True, **kwargs
    ):
        """Günstigsten Preis aus Kundenpreisliste und globalen Preislisten.

        Verglichen werden:

        1. die Preisliste des Angebots bzw. Auftrags (Kundenpreisliste),
        2. alle Regeln der als "Global berücksichtigen" markierten
           Preislisten (Default mit den Staffelpreisen aus dem Produkt-Reiter
           "Preise", Mengenstaffeln).

        Regeln anderer Preislisten (kundenspezifische Preise) gelten nur für
        Angebote mit genau dieser Preisliste.

        Für nicht rabattfähige Produkte sind Rabattregeln bereits über
        `product.pricelist.item._is_applicable_for` ausgeschlossen.

        Rückgabe wie im Standard: {product_id: (price, rule_id)}. Die Regel
        des niedrigsten Preises wird zurückgegeben, weil `sale.order.line`
        in Odoo 19 nur die Regel (`pricelist_item_id`) verwendet. Auch bei
        `compute_price=False` werden die Preise intern berechnet. Bei
        Gleichstand gewinnt die Kundenpreisliste.
        """
        if not self or self.env.context.get(SKIP_GLOBAL_QUANTITY_KEY):
            return super()._compute_price_rule(
                products, quantity, currency=currency, uom=uom, date=date,
                compute_price=compute_price, **kwargs
            )

        self.ensure_one()
        if not products:
            return {}

        target_currency = currency or self.currency_id or self.env.company.currency_id
        date = date or fields.Datetime.now()

        results = super()._compute_price_rule(
            products, quantity, currency=currency, uom=uom, date=date,
            compute_price=True, **kwargs
        )

        digits = self.env["decimal.precision"].precision_get("Product Price")

        def offer(product_id, price, rule_id):
            current_price, _rule_id = results.get(product_id, (None, False))
            if current_price is None or float_compare(
                price, current_price, precision_digits=digits
            ) < 0:
                results[product_id] = (price, rule_id)

        # Global markierte Preislisten (Default, Mengenstaffeln)
        global_pricelists = self._get_global_quantity_pricelists(target_currency)
        for global_pricelist in global_pricelists:
            global_results = global_pricelist.with_context(
                **{SKIP_GLOBAL_QUANTITY_KEY: True}
            )._compute_price_rule(
                products, quantity, currency=target_currency, uom=uom,
                date=date, compute_price=True, **kwargs
            )
            for product_id, (price, rule_id) in global_results.items():
                # Ohne passende Regel liefert Odoo nur den Listenpreis.
                if rule_id:
                    offer(product_id, price, rule_id)

        if not compute_price:
            results = {
                product_id: (0.0, rule_id)
                for product_id, (_price, rule_id) in results.items()
            }

        return results
