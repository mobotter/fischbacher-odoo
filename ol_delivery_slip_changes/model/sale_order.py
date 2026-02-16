from odoo import fields , models , api 

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_door = fields.Text(string="Bestellt durch")
    print_delivery_address = fields.Boolean(string="Print Delivery Address?", default=False)