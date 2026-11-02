from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_update_prices_lines(self):
        """Festpreise von "Preise aktualisieren" ausnehmen.

        Odoo 19 ruft `_compute_price_unit` dort mit
        `force_price_recomputation=True` auf und setzt den Rabatt auf 0,
        bevor er neu berechnet wird. Festpreispositionen bleiben unverändert.
        """
        lines = super()._get_update_prices_lines()
        return lines.filtered(
            lambda line: not line._is_protected_fixed_price()
        )
