# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class Instance(models.Model):
    _inherit = "zbs.instance"

    button_action_model = fields.Char()
    button_action_id = fields.Integer()
