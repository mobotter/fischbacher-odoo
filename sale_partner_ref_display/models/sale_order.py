from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_product_id_change(self):
        super()._compute_product_id_change()
        for line in self:
            if line.product_id:
                product = line.product_id
                code = product.default_code or ''
                name = product.name or ''
                line.name = f"{code} - {name}" if code else name
