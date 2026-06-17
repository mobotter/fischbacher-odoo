from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    barcode_scan = fields.Char(string='Barcode Scan', copy=False)

    def _merge_duplicate_barcode_lines(self):
        for order in self:
            grouped = {}
            lines_to_remove = self.env['sale.order.line']

            for line in order.order_line.filtered(lambda l: not l.display_type and l.product_id):
                key = line.product_id.id
                if key not in grouped:
                    grouped[key] = line
                    continue

                grouped[key].product_uom_qty += line.product_uom_qty
                lines_to_remove |= line

            if lines_to_remove:
                lines_to_remove.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._merge_duplicate_barcode_lines()
        return orders

    def write(self, vals):
        res = super().write(vals)
        self._merge_duplicate_barcode_lines()
        return res
