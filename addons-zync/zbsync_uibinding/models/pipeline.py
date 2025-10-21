# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models

# TODO add list action in 16.0


class Pipeline(models.Model):
    _inherit = "zbs.pipeline"

    button_ids = fields.One2many("zbs.pipeline.button", "pipeline_id", string="Buttons")

    def unlink(self):
        self.button_ids.unlink()
        return super().unlink()
