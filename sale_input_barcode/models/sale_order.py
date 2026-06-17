from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    barcode_scan = fields.Char(string='Barcode Scan', copy=False)

    @api.model
    def _barcode_product_domain(self, barcode):
        return [('barcode', '=', barcode), ('sale_ok', '=', True)]

    def _prepare_sale_line_from_product(self, product):
        self.ensure_one()
        line = self.env['sale.order.line'].new({
            'order_id': self.id,
            'product_id': product.id,
            'product_uom_qty': 1.0,
        })
        if hasattr(line, '_onchange_product_id'):
            line._onchange_product_id()
        vals = line._convert_to_write(line._cache)
        vals.update({
            'order_id': self.id,
            'product_id': product.id,
            'product_uom_qty': 1.0,
        })
        return vals

    def action_process_barcode_scan(self):
        self.ensure_one()
        barcode = (self.barcode_scan or '').strip()
        if not barcode:
            return False
        if not self.partner_id:
            self.barcode_scan = False
            raise UserError(_('Please select a customer before scanning products.'))

        product = self.env['product.product'].search(self._barcode_product_domain(barcode), limit=1)
        if not product:
            self.barcode_scan = False
            raise UserError(_('No saleable product found for barcode: %s') % barcode)

        vals = self._prepare_sale_line_from_product(product)
        self.env['sale.order.line'].create(vals)
        self.barcode_scan = False
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
