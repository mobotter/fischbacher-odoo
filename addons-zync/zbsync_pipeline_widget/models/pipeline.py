# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
from odoo import fields, models


class Pipeline(models.Model):
    _inherit = "zbs.pipeline"

    renderer = fields.Text(compute="_compute_rendercontent")

    def _compute_rendercontent(self):
        for rec in self:
            content = []
            for line in rec.line_ids.sorted():
                content.append(line.compute_rendercontent())
            self.renderer = json.dumps(content)
