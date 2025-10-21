from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools.safe_eval import safe_eval
import logging
from datetime import datetime


class Decision(models.Model):
    _inherits = {"of.base.item": "item_id"}
    _inherit = ["of.base.item.abstract"]
    _name = "of.decision"
    _description = "Flows Decision"

    # TODO sequence und else zweig am ende
    # TODO im diagram den zweig mit condition beschriften

    def _show_condition(self):
        self.write({"show_condition": True})

    def _has_code(self):
        self.write({"has_code": False})

    def _heartbeat(self, instance_item, additional_data):
        super()._heartbeat(instance_item, additional_data)

        nextones = self.env["of.connection"]
        for outgoing in self.outgoing_ids:
            if outgoing.applies(instance_item):
                nextones |= outgoing

        if nextones:
            instance_item._goto_next(forced=nextones)
