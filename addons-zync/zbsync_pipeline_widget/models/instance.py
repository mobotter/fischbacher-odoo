# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
from odoo import fields, models
from odoo.models import NewId


def serializer(obj):
    if isinstance(obj, NewId):
        return obj.origin
    return obj


class Instance(models.Model):
    _inherit = "zbs.instance"

    renderer = fields.Text(compute="_compute_rendercontent")

    def _compute_rendercontent(self):
        for rec in self:
            content = []
            for line in rec.line_ids.sorted():
                json_line = line.compute_rendercontent()
                content.append(json_line)
            self.renderer = json.dumps(content, default=serializer)
