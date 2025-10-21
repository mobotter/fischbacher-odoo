# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class ZBSDumperTestPartner(models.Model):
    _name = "zbs.test.partner"
    _description = "Unittest Zync Test Partner"

    parent_partner_id = fields.Many2one("zbs.test.partner")
    line_ids = fields.One2many("zbs.test.order.line", "order_id")
    name = fields.Char()
    anyfield = fields.Char()
    tag_ids = fields.Many2many("zbs.test.tag")
