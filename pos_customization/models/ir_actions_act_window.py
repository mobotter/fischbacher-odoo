from odoo import fields , models 


class ActionWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    limit = fields.Integer(default=200, help='Default limit for the list view')
