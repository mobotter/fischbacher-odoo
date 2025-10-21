# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class ZbsStop(models.Model):
    _inherit = "zbs.stop"

    description = fields.Char("Description")

    def process(self, instance, data, errors=None):
        if data and data[0]:
            self._check_response_data(instance, data)
        res = super().process(instance, data, errors=errors)

        return res

    def _check_response_data(self, instance, data):
        config = self._get_config(instance)
        if config:
            config._check_response_data(data)

    def _get_config(self, instance):
        start = instance.line_ids.filtered(lambda x: x.worker_id._name == "zbs.start")
        config = (
            self.env[start.worker_id._name].browse(start.worker_id.id).rest_config_id
        )
        return config
