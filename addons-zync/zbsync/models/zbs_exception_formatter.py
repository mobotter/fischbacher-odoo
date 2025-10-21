# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import traceback
import json
from odoo import api, models


class ExceptionFormatter(models.Model):
    _name = "zbs.exception.formatter"
    _description = "Zync Exception Formatter"

    @api.model
    def _structure(self, exception):
        """
        Override explicitly allowed.
        Try to make as base as possible a readable json struct
        with precise information.

        """
        res = {}
        res["str"] = str(exception)
        res["traceback"] = traceback.format_exception(
            exception, value=exception, tb=exception.__traceback__
        )
        res["record"] = getattr(exception, "zbs_record", None)
        return res

    def as_json(self, exception):
        struct = self._structure(exception)
        j = json.dumps(struct, indent=4)
        return j
