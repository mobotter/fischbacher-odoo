# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class Pipeline(models.Model):
    _inherit = "zbs.pipeline"

    method_trigger_ids = fields.One2many(
        "zbs.trigger.methodhook",
        "pipeline_id",
        string="Triggers",
    )

    field_trigger_ids = fields.One2many(
        "zbs.trigger.fieldhook",
        "pipeline_id",
        string="Field Trigger",
    )
