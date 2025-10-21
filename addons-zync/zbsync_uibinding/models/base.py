# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def start_action_zbsync_from_button(self):
        active_id = self.env.context.get("active_id")
        model = self.env.context.get("active_model")
        if not active_id:
            instance = self
        else:
            instance = self.env[model].browse(active_id)
        button_action = (
            self.env["zbs.pipeline.button"]
            .sudo()
            .browse(self.env.context["button_action_id"])
            .ensure_one()
        )
        action = button_action._start(instance)

        return action
