# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import uuid
from odoo import api, fields, models
import base64
import json


class WizImportPipeline(models.Model):
    _inherit = "mixin.diffview"
    _name = "zbs.import.pipeline"
    _description = "Pipeline Import Wizard"

    filename = fields.Char("Filename")
    filecontent = fields.Binary("JSON Content")
    diffcontent = fields.Text(compute="_compute_diffcontent")
    pipeline_id = fields.Many2one("zbs.pipeline", "Pipeline")
    newname = fields.Char("New Name")
    log = fields.Text()

    @api.onchange("filecontent")
    def _uploaded_file(self):
        if not self.filecontent:
            return
        filecontent = base64.b64decode(self.filecontent).decode("utf8")
        filecontent = json.loads(filecontent)
        self.pipeline_id = False
        if isinstance(filecontent, dict):
            if "__record_id" in filecontent:
                model, _ = filecontent["__record_id"].split(",")
                if model == "zbs.pipeline":
                    pipe = self.env["zbs.pipeline"].browse()
                    if filecontent.get("zync_uuid"):
                        pipe = pipe.search(
                            [("zync_uuid", "=", filecontent["zync_uuid"])]
                        )
                    if pipe:
                        self.pipeline_id = pipe

    @api.depends("filecontent", "pipeline_id")
    def _compute_diffcontent(self):
        for rec in self:
            rec.diffcontent = False
            if not rec.pipeline_id:
                continue
            if not rec.filecontent:
                continue
            pipecontent = json.dumps(rec.pipeline_id.dump(), indent=4)
            try:
                filecontent = base64.b64decode(rec.filecontent).decode("utf8")
            except Exception as ex:
                filecontent = str(ex)
            rec.diffcontent = rec._gitdiff(pipecontent, filecontent)

    def ok(self):
        content = base64.b64decode(self.filecontent).decode("utf8")
        content = json.dumps(json.loads(content), indent=8)
        if self.newname:
            content = self._remove_uuids(content)
        content = json.loads(content)
        if self.newname:
            content["name"] = self.newname

        def log(msg):
            # dont log million lines
            self.log = ((self.log or "") + f"\n{msg}").strip()

        pipeline = (
            self.env["zbs.pipeline"].with_context(zbs_import_log=log).load(content)
        )
        if any(x in (self.log or "") for x in ["WARN", "ERROR"]):
            self.pipeline_id = pipeline
            return {
                "view_type": "form",
                "res_model": self._name,
                "res_id": self.id,
                "views": [(False, "form")],
                "type": "ir.actions.act_window",
                "target": "new",
            }
        return {
            "view_type": "form",
            "res_model": pipeline._name,
            "res_id": pipeline.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def _remove_uuids(self, filecontent):
        def _random_id(line):
            if '"zync_uuid": ' in line:
                line = f'"zync_uuid": "{uuid.uuid4()}",'
            return line

        lines = list(map(_random_id, filecontent.splitlines()))
        return "\n".join(lines)

    @api.onchange("newname")
    def _changed_newname(self):
        self.pipeline_id = False
