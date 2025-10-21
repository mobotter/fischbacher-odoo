# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class ZBSConnection(models.AbstractModel):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.connection"
    _description = "Zync Xport Mixin"

    name = fields.Char("Name", required=True)


class ZBSConnectionUsernamePassword(models.AbstractModel):
    _name = "zbs.connection.mixin.usernamepassword"
    _description = "Username Password Mixin"

    username = fields.Char("Username", required=True)
    password = fields.Char("Password", required=True)


class ZBSConnectionUrl(models.AbstractModel):
    _name = "zbs.connection.mixin.url"
    _description = "URL Mixin"

    url = fields.Char("URL", required=True)


class ZBSConnectionHostPort(models.AbstractModel):
    _name = "zbs.connection.mixin.hostport"
    _description = "Host Port Mixin"

    host = fields.Char("Host", required=True)
    port = fields.Integer("Port", required=True)
