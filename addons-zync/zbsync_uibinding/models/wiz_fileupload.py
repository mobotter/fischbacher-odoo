# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models
from odoo.exceptions import UserError
import base64


class WizFileUpload(models.Model):
    _name = "zbs.wiz.fileupload"
    _description = "Wizard Fileupload Zync"

    filecontent = fields.Binary("Filecontent")
    filename = fields.Char("Filename")
    pipeline_id = fields.Many2one("zbs.pipeline", string="Pipeline")

    def ok(self):
        if not self.filecontent:
            raise UserError("Please upload a file!")
        content = base64.b64decode(self.filecontent)
        data = {
            "filename": self.filename,
            "content": content,
        }

        instance = self.pipeline_id.start(
            data,
            initiated_by="fileupload",
        )
        instance._roll_after_start()
        return {
            "view_type": "form",
            "res_model": instance._name,
            "res_id": instance.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }
