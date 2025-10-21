# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class PipelineVersion(models.Model):
    _name = "zbs.pipeline.version"
    _description = "Zync Pipeline Version"
    _order = "date desc"

    pipeline_id = fields.Many2one(
        "zbs.pipeline", xport_ignore=True, ondelete="cascade", required=True
    )

    date = fields.Datetime("Date", default=lambda self: fields.Datetime.now())
    content = fields.Text("Content")

    def download(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/zync_download_version/{self.id}",
            "target": "self",
        }
