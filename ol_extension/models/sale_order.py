from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # TASK ID: 51580
    delivery_address = fields.Text(
        string="Delivery Address 2",
        copy=True,
    )
    # TASK ID: 51580