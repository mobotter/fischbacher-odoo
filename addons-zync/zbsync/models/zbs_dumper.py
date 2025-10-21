# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class ZBSDumper(models.AbstractModel):
    _inherit = ["zbs.worker", "zbs.grabber_dumper"]
    _name = "zbs.dumper"
    _description = "Dumper (Abstract)"

    can_keys = fields.Boolean("Can Keys", compute="_compute_capas")
    can_keys_multi_ok = fields.Boolean(
        "Multiple Keys allowed", compute="_compute_capas"
    )
    can_delete_one2many = fields.Boolean(
        "Can delete one2many", compute="_compute_capas"
    )
    can_compare_delta = fields.Boolean(
        "Can compare delta",
        compute="_compute_capas",
        help="Helpds for default values at write",
    )

    def _compute_capas(self):
        for rec in self:
            rec.can_keys = False
            rec.can_keys_multi_ok = False
            rec.can_delete_one2many = False
            rec.can_compare_delta = False


class ZBSDumperMixinCU(models.AbstractModel):
    _name = "zbs.dumper.mixin.cu"
    _description = "Dumper Mixin"

    do_insert = fields.Boolean("Do Insert", default=True)
    do_update = fields.Boolean("Do Update", default=True)
