# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class FieldTrigger(models.Model):
    _name = "zbs.trigger.fieldhook"
    _description = "Event Hook for Fields"
    _inherit = [
        "zbs.trigger.methodhook",
        "method_hook.field_trigger",
        "zbs.xport.mixin",
    ]

    def _trigger(self, instances, args_packed, method):
        self._start_by_methodhook(instances, args_packed, method)
