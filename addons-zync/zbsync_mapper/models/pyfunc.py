# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class PyFunc(models.Model):
    _inherit = ["mail.thread"]
    _name = "zbs.mapping.pyfunc"
    _description = "Zync Python Function"

    code = fields.Text("Code", help="objects: record")
    name = fields.Char("Name")
