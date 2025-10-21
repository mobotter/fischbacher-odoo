# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import base64
import json
from odoo import api, fields, models


class ZbsyncEnvXport(models.TransientModel):
    _name = "zbs.env.xport"
    _description = "Export your pipeline"

    mode = fields.Selection(
        [("import", "Import"), ("export", "Export")], string="Mode", default="import"
    )
    environment_ids = fields.Many2many("zbs.environment", string="Filter Environments")
    file_content = fields.Binary("File Content")
    filename = fields.Char("Filename", compute="_compute_filename")

    @api.depends("environment_ids")
    def _compute_filename(self):
        for rec in self:
            envs = "_".join(self.environment_ids.mapped("name"))
            rec.filename = f"variables_{envs}.json"

    def do_import(self):
        content = json.loads(base64.b64decode(self.file_content))
        self.env["zbs.environment"]._import(content)
        return {
            "name": "Imported variables",
            "view_type": "form",
            "res_model": "zbs.variable.value",
            "domain": [],
            "views": [(False, "tree")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def do_export(self):
        content = self.environment_ids._export()
        content = json.dumps(content, indent=4).encode("utf8")
        self.file_content = base64.encodebytes(content)
        return {
            "view_type": "form",
            "res_model": self._name,
            "res_id": self.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res["environment_ids"] = self.env["zbs.environment"].search([]).ids
        return res
