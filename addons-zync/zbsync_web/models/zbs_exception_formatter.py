# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, models
from requests import HTTPError


class ExceptionFormatter(models.Model):
    _inherit = "zbs.exception.formatter"

    @api.model
    def _structure(self, exception):
        res = super()._structure(exception)

        if isinstance(exception, HTTPError):
            for item in ["response", "request"]:
                res.setdefault(item, {})
                d = getattr(exception, item)
                d = d is not None and d.__dict__ or {}
                for k, v in d.items():
                    try:
                        res[item][k] = str(v)
                    except Exception as ex:
                        res[item][k] = str(ex)
        return res
