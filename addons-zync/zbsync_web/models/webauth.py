# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models
from requests.auth import HTTPBasicAuth
from contextlib import contextmanager

try:
    from requests_oauth2client import BearerToken as BearerAuth
except:
    from requests_oauth2client import BearerAuth


class WebAuth(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.connection.web.auth"
    _description = "Web Connection"

    name = fields.Char("Name")
    auth_type = fields.Selection(
        [
            ("bearer_token", "Bearer Token"),
            ("basic_auth", "Basic Auth"),
            ("custom", "Custom"),
        ],
        string="Auth Type",
    )

    username = fields.Char("Username")
    password = fields.Char("Password")
    token = fields.Char("Token")

    @contextmanager
    def _do_auth(self, method, method_str, params):
        if self:
            self.ensure_one()

            func = getattr(self, "_" + self.auth_type, None)
            if not func:
                raise NotImplementedError(f"Missing: {self.auth_type}")
            func(params)
            if "pyrequests" in params:
                requests = params.pop("pyrequests")
                method = getattr(requests, method_str)

        yield method

    def _basic_auth(self, params):
        basic = HTTPBasicAuth(self.username, self.password)
        params["auth"] = basic

    def _bearer_token(self, params):
        params["auth"] = BearerAuth(self.token)

    def name_get(self):
        res = []
        for auth in self:
            name = f"{auth.name} - {auth.auth_type}"
            res += [(auth.id, name)]
        return res
