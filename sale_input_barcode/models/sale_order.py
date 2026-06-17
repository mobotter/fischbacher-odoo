from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    barcode_scan = fields.Char(string='Barcode Scan', copy=False)

    @api.model
    def _barcode_product_domain(self, barcode):
        return [('barcode', '=', barcode), ('sale_ok', '=', True)]
