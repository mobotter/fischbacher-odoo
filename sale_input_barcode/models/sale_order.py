from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    barcode_scan = fields.Char(string='Barcode Scan', copy=False)

    @api.model
    def _barcode_product_domain(self, barcode):
        return [('barcode', '=', barcode), ('sale_ok', '=', True)]

    def action_process_barcode_scan(self):
        for order in self:
            barcode = (order.barcode_scan or '').strip()
            if not barcode:
                continue
            if not order.partner_id:
                order.barcode_scan = False
                raise UserError(_('Please select a customer before scanning products.'))

            product = self.env['product.product'].search(order._barcode_product_domain(barcode), limit=1)
            if not product:
                order.barcode_scan = False
                raise UserError(_('No saleable product found for barcode: %s') % barcode)

            line = self.env['sale.order.line'].new({
                'order_id': order.id,
                'product_id': product.id,
                'product_uom_qty': 1.0,
            })
            line.product_id_change()
            vals = line._convert_to_write(line._cache)
            vals.update({
                'order_id': order.id,
                'product_id': product.id,
                'product_uom_qty': 1.0,
            })
            self.env['sale.order.line'].create(vals)
            order.barcode_scan = False
        return True

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        if self.barcode_scan:
            self.action_process_barcode_scan()
