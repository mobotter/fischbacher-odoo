# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models
from requests import Session
from requests.auth import HTTPBasicAuth


class SoapConnection(models.Model):
    _inherit = [
        "zbs.connection",
        "zbs.connection.mixin.usernamepassword",
    ]
    _name = "zbs.connection.soap"
    _description = "SOAP-Connection"

    wsdl_url = fields.Char("WSDL Url")
    name = fields.Char(related="wsdl_url", required=False)
    username = fields.Char(required=False)
    password = fields.Char(required=False)
    timeout = fields.Integer("Timeout")

    def _create_session(self):
        session = Session()
        if self.username:
            session.auth = HTTPBasicAuth(self.username, self.password)
        return session
