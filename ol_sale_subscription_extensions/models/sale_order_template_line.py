from odoo import fields, models


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    price_unit = fields.Float(string="Unit Price", digits="Product Price")
