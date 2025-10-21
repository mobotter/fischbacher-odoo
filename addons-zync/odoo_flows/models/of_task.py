from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools.safe_eval import safe_eval


class Task(models.Model):
    _inherit = ["of.base.item.abstract"]
    _inherits = {"of.base.item": "item_id"}
    _name = "of.task"
    _description = "Flows Task"

    def _has_code(self):
        self.write({"has_code": True})

    def _heartbeat(self, instance_item, additional_data):
        self.ensure_one()
        self._eval(
            instance_item=instance_item, requires_result=False, **additional_data
        )
        instance_item._goto_next()
