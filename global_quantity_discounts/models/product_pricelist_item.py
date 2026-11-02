# Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _is_customer_discount_rule(self):
        """True, wenn die Regel einen Rabatt gewährt.

        * `percentage` mit positivem Prozentsatz (negativer Wert = Aufschlag)
        * `formula` auf Basis Verkaufspreis/Preisliste mit positivem Rabatt
          oder negativem Aufschlagsbetrag

        `fixed` (Festpreis) und Kosten-plus-Aufschlag-Formeln sind keine
        Rabatte.
        """
        self.ensure_one()

        if self.compute_price == "percentage":
            return self.percent_price > 0

        if self.compute_price == "formula" and self.base != "standard_price":
            return self.price_discount > 0 or self.price_surcharge < 0

        return False

    def _is_applicable_for(self, product, qty_in_product_uom):
        """Nicht rabattfähige Produkte erhalten keine Rabattregeln.

        Gilt für alle Preislisten, auch für Mengenstaffeln und Regeln aus dem
        Produkt-Reiter "Preise". Da Odoo die erste passende Regel verwendet,
        greift danach automatisch die nächste passende Regel (z. B. ein
        Festpreis) bzw. der Listenpreis.
        """
        res = super()._is_applicable_for(product, qty_in_product_uom)

        if (
            res
            and not product.discount_allowed
            and self._is_customer_discount_rule()
        ):
            return False

        return res
