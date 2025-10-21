# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class ZbsyncTransformer(models.Model):
    _inherit = ["zbs.transformer.python", "code.helper.mixin"]
    _name = "zbs.transformer.python"
