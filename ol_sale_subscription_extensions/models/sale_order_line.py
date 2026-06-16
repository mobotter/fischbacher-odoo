from odoo import models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        # Odoo hängt den Abrechnungszeitraum per \n an den Produktnamen:
        # description += f"\n{duration} {start_to_next}"
        # Quelle: enterprise/sale_subscription/models/sale_order_line.py
        name = res.get('name', '')
        if name and '\n' in name:
            res['name'] = name.split('\n')[0]
        return res
