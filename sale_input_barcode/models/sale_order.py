from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    barcode_scan = fields.Char(string='Barcode Scan', copy=False)
