# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class Encoding(models.Model):
    _name = "zbs.encoding"
    _description = "Character Encoding"
    name = fields.Char("Encoding", required=True)
