# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class WebWorkerHeader(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.web.request_args"
    _table = "zbs_web_worker_header"
    _description = "HTTP Request Arguments (Header, Cookies, etc.)"

    worker_id = fields.Many2one("zbs.web.worker", string="Worker", xport_ignore=True)

    type = fields.Selection(
        [
            ("header", "Header"),
            ("cookie", "Cookie"),
        ],
        default="header",
        string="Type",
        required=True,
    )
    name = fields.Char("Name", required=True)
    value = fields.Text("Value", required=True)
