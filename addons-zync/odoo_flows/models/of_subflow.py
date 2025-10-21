from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools.safe_eval import safe_eval
import logging
from datetime import datetime


class Subflow(models.Model):
    _inherits = {"of.base.item": "item_id"}
    _inherit = ["of.base.item.abstract"]
    _name = "of.subflow"
    _description = "Flows Sub Flow"

    subflow_id = fields.Many2one("of.flow", string="SubFlow")

    def _heartbeat(self, instance_item, additional_data):
        super()._heartbeat(instance_item, additional_data)

        if not instance_item.subflow_instance_created:
            instance_item.subflow_instance_created = True
            instance_item.subflow_instance_id = self.subflow_id.start(
                instance_item._odoo_instance
            )
        else:
            if not instance_item.subflow_instance_id.active:
                instance_item._goto_next()
