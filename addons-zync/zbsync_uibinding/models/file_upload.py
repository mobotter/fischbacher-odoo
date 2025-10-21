# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class Fileupload(models.Model):
    _name = "zbs.pipeline.fileupload"
    _description = "Zync UI Fileupload"

    pipeline_id = fields.Many2one(
        "zbs.pipeline", string="Pipeline", ondelete="cascade", required=True
    )
    parent_menu_id = fields.Many2one(
        "ir.ui.menu", string="Parent Menu", xport_ignore=True
    )
    created_window_action_ids = fields.One2many(
        "ir.actions.act_window", "fileupload_id", xport_ignore=True
    )
    created_menu_item_ids = fields.One2many(
        "ir.ui.menu", "fileupload_id", xport_ignore=True
    )

    def create_entry(self):
        self = self.sudo()
        window_act = self.env["ir.actions.act_window"].create(
            {
                "res_model": "zbs.wiz.fileupload",
                "target": "new",
                "context": {"default_pipeline_id": self.pipeline_id.id},
                "view_mode": "form",
                "fileupload_id": self.id,
            }
        )
        mi = self.env["ir.ui.menu"].create(
            {
                "name": f"{self.pipeline_id.name} File Upload",
                "parent_id": self.parent_menu_id.id,
                "action": f"{window_act._name},{window_act.id}",
                "fileupload_id": self.id,
            }
        )
        self.created_window_action_ids = [(4, window_act.id)]
        self.created_menu_item_ids = [(4, mi.id)]
