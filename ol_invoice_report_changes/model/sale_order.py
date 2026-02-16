from odoo import fields , models , api 

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_no = fields.Char(string="Purchase")
    order_number = fields.Char(string="Order Number")
    is_rent = fields.Boolean(string="Rent")
    hide_total = fields.Boolean(string="Hide Total Amount")
    german_payment_term = fields.Char(string="Zahlungsbedingungen")


    # Task Id 33897 JC
    # client_order_name = fields.Text(string="Ordered by")
    # client_order_number = fields.Char(string=" Your Order Number")

