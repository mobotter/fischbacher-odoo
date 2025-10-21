# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class PipelineTag(models.Model):
    _name = "zbs.pipeline.tag"
    _description = "Zync Tags"

    name = fields.Char("Name", required=True)
    color = fields.Integer("Color", default=0)
