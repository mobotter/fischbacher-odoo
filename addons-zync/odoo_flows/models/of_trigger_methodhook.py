from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools.sql import table_exists
from odoo.tools.safe_eval import safe_eval
import inspect
from collections import defaultdict
import logging


class TriggerMethodHook(models.Model):
    _inherit = "method_hook.trigger.mixin"
    _name = "of.trigger.methodhook"
    _description = "Flows Trigger Methodhook"

    trigger_id = fields.Many2one("of.trigger", string="Trigger", ondelete="cascade")

    def _trigger(self, instances, *args, **kwargs):
        self.trigger_id._start_by_methodhook(instances)
