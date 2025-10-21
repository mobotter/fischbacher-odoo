# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, fields, models
from odoo.exceptions import AccessDenied
from .. import URL


class StartElement(models.Model):
    _inherit = "zbs.start"

    url = fields.Char("URL", compute="_compute_url")
    identifier = fields.Char("Identifier")
    authorizer_id = fields.Many2one("zbs.receive.authorizer", "Authorizer")
    request_method = fields.Selection(
        [("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("DELETE", "DELETE")],
        string="Request Type",
    )
    request_type = fields.Selection(
        [
            ("application/json", "application/json"),
            ("application/text", "application/text"),
        ],
        string="Payload Type",
        default="application/json",
    )
    force_user_id = fields.Many2one("res.users", string="Force User")

    @api.depends("identifier")
    def _compute_url(self):
        for rec in self:
            url = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param(key="web.base.url", default=False)
            )
            if rec.identifier:
                url += URL + rec.identifier
            else:
                url = False
            rec.url = url

    def authorize_webrequest(self, headers, postdata, keyvalues):
        self.ensure_one()
        if not self.authorizer_id:
            default_user = self.env.ref("base.public_user")
            default = {"odoo_user_id": default_user.id}
            return {
                "authorized": True,
                "method": "everything for free",
                "payload": default,
            }

        res = self.authorizer_id.authorize_webrequest(headers, postdata, keyvalues)
        if not res:
            raise AccessDenied()
        return res
