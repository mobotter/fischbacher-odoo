# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class BaseWizard(models.AbstractModel):
    _name = "zbsync.base_wizard"
    _description = "Abstract Base Wizard"

    name = fields.Char(default="Name the wizard")
    sample_file = fields.Binary("Sample File")

    def fill_pipeline(self):
        raise NotImplementedError("Create me")

    def button_ok(self):
        pipeline = self.env["zbs.pipeline"].create({})

        self.fill_pipeline(pipeline)

        return {
            "view_type": "form",
            "res_model": pipeline._name,
            "res_id": pipeline.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }
