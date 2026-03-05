from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
# task id 33982 JC
    reverse_charge = fields.Boolean(
        string="Reverse Charge",
        help="Enable this if the partner is subject to reverse charge mechanism."
    )
    #  task id 33982 JC
