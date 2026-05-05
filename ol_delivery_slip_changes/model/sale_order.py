from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_door = fields.Text(string="Bestellt durch")
    print_delivery_address = fields.Boolean(string="Print Delivery Address?", default=False)
    purchase_no_backup = fields.Char(string="Purchase")
    order_number_backup = fields.Char(string="Order Number")
    is_rent_backup = fields.Boolean(string="Rent")
    hide_total_backup = fields.Boolean(string="Hide Total Amount")
    german_payment_term_backup = fields.Char(string="Zahlungsbedingungen")

    # Fehlende Felder aus Template-Referenzen hinzugefügt
    client_order_name = fields.Char(string="Ordered by")
    client_order_number = fields.Char(string="Your Order Number")
    client_order_ref = fields.Text(string="Project / Customer Ref")
