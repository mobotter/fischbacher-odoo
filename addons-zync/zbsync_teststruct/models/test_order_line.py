# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class ZBSDumperTestStructLine(models.Model):
    _name = "zbs.test.order.line"
    _description = "Unittest Zync Test Order Line"
    order_id = fields.Many2one("zbs.test.order")
    name = fields.Char()
    price = fields.Float()
    anyfield = fields.Char()
