# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, fields, models


class DupWizard(models.Model):
    _name = "zbs.dup.wizard"
    _description = "Zync Make Copy Wizard"

    src_pipeline_id = fields.Many2one("zbs.pipeline")

    line_ids = fields.One2many("zbs.dup.wizard.line", "wiz_id")

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        for rec in res:
            for line in rec.src_pipeline_id.line_ids:
                rec.line_ids = [
                    [
                        0,
                        0,
                        {
                            "wiz_id": rec.id,
                            "worker_id": f"{line.worker_id._name},{line.worker_id.id}",
                            "line_id": line.id,
                        },
                    ]
                ]

        return res

    def duplicate(self):
        pipeline = self.src_pipeline_id.with_context(zync_import=True).copy(
            {"line_ids": [[5]]}
        )
        assert not pipeline.line_ids
        for line in self.line_ids.sorted():
            values = {"pipeline_id": pipeline.id}
            if line.mode == "copy":
                worker = line.line_id.worker_id.copy()
            else:
                worker = line2.worker_id.id
            values["worker_id"] = f"{worker._name},{worker.id}"
            line2 = line.line_id.with_context(zync_import=True).copy(values)
        return {
            "view_type": "form",
            "res_model": pipeline._name,
            "res_id": pipeline.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "context": {
                "form_view_initial_mode": "edit",
                "action_buttons": False,
            },
            "target": "current",
        }


class DupWizardLine(models.Model):
    _name = "zbs.dup.wizard.line"
    _description = "Zync duplicate wizard line"
    _line = "Zync Duplicate Wizard Line"
    _order = "sequence"

    name = fields.Char(related="line_id.name")
    wiz_id = fields.Many2one("zbs.dup.wizard", required=True)
    sequence = fields.Integer(related="line_id.sequence")

    line_ids = fields.One2many("zbs.dup.wizard.line", "wiz_id", string="Wizard Line")
    line_id = fields.Many2one("zbs.pipeline.line", string="Pipeline Line")
    worker_id = fields.Reference(related="line_id.worker_id")
    mode = fields.Selection(
        [("copy", "Copy"), ("use", "Use")], string="Mode", default="copy"
    )
