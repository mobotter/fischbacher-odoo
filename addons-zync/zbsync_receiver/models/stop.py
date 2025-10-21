# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class Stop(models.Model):
    _inherit = "zbs.stop"

    return_data = fields.Boolean("Return Data")
    content_type = fields.Char("Content Type", default="application/json")
    force_return_object = fields.Boolean("Force Object Return")

    def process(self, instance, data, errors=None):
        res = super().process(instance, data, errors=errors)
        if not self.return_data:
            res = instance.Result(None)
        return res
