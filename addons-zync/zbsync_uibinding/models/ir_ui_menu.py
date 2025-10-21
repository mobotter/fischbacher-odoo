# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class Menu(models.Model):
    _inherit = "ir.ui.menu"

    fileupload_id = fields.Many2one("zbs.pipeline.fileupload", string="Pipeline")
