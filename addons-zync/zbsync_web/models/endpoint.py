# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class Endpoint(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.web.endpoint"
    _description = "Web Endpoint"
