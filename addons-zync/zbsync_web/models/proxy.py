# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class Proxy(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.web.proxy"
    _description = "Web Proxy"

    name = fields.Char("Name", required=True)

    protocol = fields.Selection(
        [
            ("http", "http"),
            ("https", "https"),
        ],
        string="Protocol",
        required=True,
    )
    url = fields.Char("URL", required=True)

    def _get_for_requests(self):
        res = {}
        for rec in self:
            res[rec.protocol] = rec.url
        return res
