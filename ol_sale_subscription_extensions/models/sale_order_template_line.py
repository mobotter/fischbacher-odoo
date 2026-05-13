from odoo import fields, models


class SaleOrderTemplateLine(models.Model):
    _inherit = "sale.order.template.line"

    price_unit = fields.Float(string="Unit Price", digits="Product Price")
    discount = fields.Float(string="Discount (%)", digits="Discount", default=0.0)
    tax_id = fields.Many2many(
        'account.tax',
        string="Taxes",
        domain="[('type_tax_use', '=', 'sale')]",
    )
