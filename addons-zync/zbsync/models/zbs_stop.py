# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import api, models


class ZBSStop(models.Model):
    _inherit = "zbs.worker"
    _name = "zbs.stop"
    _description = "Stop your Pipeline"

    def is_end(self):
        return False

    def process(self, instance, data, errors=None):
        return instance.Result(data)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if not rec.name:
                rec.name = "-"
        return res
