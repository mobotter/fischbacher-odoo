# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class Instance(models.Model):
    _inherit = "zbs.instance"

    def _build_http_response(self):
        response = super()._build_http_response()
        data = response["body"]
        data = self.env["zebrooset"].get_python_type(data)
        line = self.next_line_id
        force_return_object = False
        if line.worker_id._name == "zbs.stop":
            force_return_object = line.worker_id.force_return_object
        if data and isinstance(data, list) and force_return_object:
            if isinstance(data, list):
                try:
                    data = data[0]
                except IndexError:
                    pass
                else:
                    response["body"] = data
        return response
