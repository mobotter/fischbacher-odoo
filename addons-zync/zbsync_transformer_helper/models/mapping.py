# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class Mappings(models.Model):
    _inherit = ["zbs.mapping", "code.helper.mixin"]
    _name = "zbs.mapping"
