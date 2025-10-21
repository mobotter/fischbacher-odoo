# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class ZBSDumperTestStruct(models.Model):
    _name = "zbs.test.order"
    _description = "Unittest Zync Test Order"

    tag_ids = fields.Many2many("zbs.test.tag")
    partner_id = fields.Many2one("zbs.test.partner")
    line_ids = fields.One2many("zbs.test.order.line", "order_id")
    name = fields.Char()

    def write(self, vals):
        res = super().write(vals)
        return res
