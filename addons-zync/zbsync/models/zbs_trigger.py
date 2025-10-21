# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class ZBSTrigger(models.AbstractModel):
    _name = "zbs.trigger"
    _description = "Trigger"

    pipeline_id = fields.Many2one("zbs.pipeline", string="Pipeline")
