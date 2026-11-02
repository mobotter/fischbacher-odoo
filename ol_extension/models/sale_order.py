from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_address = fields.Text(
        string="Delivery Address 2",
        copy=True,
    )

    delivery_time = fields.Text(
        string="Delivery time",
        help="Specify the estimated delivery time. This information will be displayed on the quotation and sales order.",
    )
