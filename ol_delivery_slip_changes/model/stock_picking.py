from odoo import fields, models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_description_report = fields.Boolean(string="Hide Description", default=False)
