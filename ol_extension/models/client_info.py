from odoo import models, fields

# Task ID: 51016
class ClientInfo(models.Model):
    _name = "client.info"
    _description = "Client Info Lines"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    pos = fields.Char(string="Pos")
    info = fields.Char(string="Info")
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        ondelete="cascade",
        index=True,
    )
# Task ID: 51016