from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        """
        Überschreibt die Rechnungszeilen-Vorbereitung für Abonnements.
        Entfernt den automatisch hinzugefügten Abrechnungszeitraum
        (z.B. "4 Woche(n) 08.06.2026 bis 05.07.2026") aus der Beschreibung.
        """
        res = super()._prepare_invoice_line(**optional_values)

        if self.order_id.is_subscription:
            name = res.get('name', '')
            # Odoo hängt den Zeitraum per Zeilenumbruch an den Produktnamen an
            if '\n' in name:
                res['name'] = name.split('\n')[0]

        return res
