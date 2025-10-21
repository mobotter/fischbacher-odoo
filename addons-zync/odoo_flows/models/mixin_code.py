from odoo import _, api, fields, models, SUPERUSER_ID
import traceback
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import arrow
import re
from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging

logger = logging.getLogger(__name__)


class CodeMixin(models.AbstractModel):
    _name = "of.mixin.code"
    _description = "Flows Mixin Code"

    code = fields.Text("Code")

    def _get_params(self, instance_item):
        def datify(x):
            return x and arrow.get(x) or False

        return {
            "obj": instance_item._odoo_instance,
            "instance_item": instance_item,
            "started": datify(instance_item.date_started),
            "deadline": datify(instance_item.deadline),
            "deadline_days": instance_item.item_id.deadline_days,
            "now": arrow.utcnow(),
        }

    def _eval(self, code=None, code_field=None, requires_result=True, **params):
        """
        False --> result = False

        """
        self.ensure_one()
        result_dict = {}

        code = code or self[code_field or "code"]
        if not code:
            code = "False"

        code = "\n".join([x for x in code.split("\n") if not x.startswith("#")])
        code = code.strip()

        if requires_result:
            if "result=" not in code and "result =" not in code:
                before, last_line = code.split("\n")[:-1], code.split("\n")[-1]
                if "result =" not in last_line:
                    last_line = f"result = {last_line}"
                code = "\n".join(before) + "\n" + last_line

        code = "\n".join(map(lambda x: f"    {x}", code.split("\n")))
        code = (
            "def convert():\n"
            "    result = None\n"
            f"{code}\n"
            "    return result\n"
            "result_dict['result'] = convert()"
        )

        def format_date(x):
            return arrow.get(x).strftime(DTF)

        def parse_date(x, default=None):
            if not x:
                return default
            return arrow.get(x)

        try:
            if "instance_item" in params:
                params.update(self._get_params(params["instance_item"]))
            params.update(
                {
                    "result_dict": result_dict,
                    "env": self.env,
                    "fields": fields,
                    "arrow": arrow,
                    "datetime": datetime,
                    "date": date,
                    "timedelta": timedelta,
                    "format_date": format_date,
                    "re": re,
                    "now": arrow.utcnow(),
                    "parse_date": parse_date,
                    "logger": logger,
                }
            )
            exec(code, params)

        except Exception as ex:
            msg = traceback.format_exc()
            msg = f"ERROR at Code: {self.code}" f"Error Message: {str(ex)} "
            raise Exception(msg) from ex

        result = result_dict["result"]
        return result
