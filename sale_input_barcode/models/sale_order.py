from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    barcode_input = fields.Char(string='Scan barcode', help='Scan a product barcode to add a new sale order line.')

    @api.model
    def _barcode_product_domain(self, barcode):
        return [('barcode', '=', barcode), ('sale_ok', '=', True)]

    def action_open_barcode_scanner_dialog(self):
        self.ensure_one()
        return True

    def action_add_product_by_barcode(self, barcode):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_('Please select a customer before scanning products.'))
        if not barcode:
            raise UserError(_('No barcode received.'))

        product = self.env['product.product'].search(self._barcode_product_domain(barcode), limit=1)
        if not product:
            raise UserError(_('No saleable product found for barcode: %s') % barcode)

        line = self.env['sale.order.line'].new({
            'order_id': self.id,
            'product_id': product.id,
            'product_uom_qty': 1.0,
        })
        line.product_id_change()
        vals = line._convert_to_write(line._cache)
        vals.update({
            'order_id': self.id,
            'product_id': product.id,
            'product_uom_qty': 1.0,
        })
        self.env['sale.order.line'].create(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Product added'),
                'message': _('%s added as a new order line.') % product.display_name,
                'type': 'success',
                'sticky': False,
            }
        }
