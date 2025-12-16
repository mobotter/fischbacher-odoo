from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    # Task ID: 51016
    client_info_ids = fields.One2many(
        comodel_name="client.info",
        inverse_name="partner_id",
        string="Client Info Lines",
        copy=True,
    )
    # Task ID: 51016

    # TASK ID: 51827
    short_term = fields.Char("Short Term")
    # TASK ID: 51827