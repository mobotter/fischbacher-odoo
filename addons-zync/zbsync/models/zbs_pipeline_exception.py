# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import api, fields, models
from ..exceptions import ZBSPipelineException


class PipelineException(models.Model):
    _name = "zbs.pipeline.exception"
    _description = "Zync Pipeline Exception"

    code = fields.Char("Error Code", required=True)
    name = fields.Char("Shortname", required=True)
    description = fields.Text("Description")
    url = fields.Char("Link")

    @api.model
    def _raise(self, code):
        exc = self.search([("code", "=", code)], limit=1)
        raise ZBSPipelineException(exc.code, exc.name)
