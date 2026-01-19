from odoo import fields , models , api 

class SaleOrder(models.Model):
    _inherit = 'stock.picking'

    is_description_report = fields.Boolean(string="Hide Description", default=False)