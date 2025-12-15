from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    # TASK ID: 51827
    short_term = fields.Char("Short Term")
    # TASK ID: 51827