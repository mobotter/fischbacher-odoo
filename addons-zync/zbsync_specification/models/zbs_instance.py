# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class ZbsInstance(models.Model):
    _inherit = "zbs.instance"

    def _get_config(self):
        start = self.line_ids.filtered(lambda x: x.worker_id._name == "zbs.start")
        config = (
            self.env[start.worker_id._name].browse(start.worker_id.id).rest_config_id
        )
        return config

    # TODO Please remove and link to force_return_object
    def _build_http_response(self):
        response = super()._build_http_response()
        config = self._get_config()
        data = response["body"]
        data = self.env["zebrooset"].get_python_type(data)
        if (
            data
            and isinstance(data, list)
            and config
            and config.response_id.content_scheme_id.property_type_id.name == "object"
        ):
            if isinstance(data, list):
                try:
                    data = data[0]
                except IndexError:
                    pass
                else:
                    response["body"] = data
        return response
