# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class ZBSDumperTestTag(models.Model):
    _name = "zbs.test.tag"
    _description = "Unittest Zync Test Tag"

    name = fields.Char()
    anyfield = fields.Char()

    def write(self, vals):
        res = super().write(vals)
        return res
