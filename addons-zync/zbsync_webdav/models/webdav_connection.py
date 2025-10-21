# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models
from webdav3.client import Client


class WebdavConnection(models.Model):
    _inherit = [
        "zbs.connection",
        "mail.thread",
    ]
    _name = "zbs.connection.webdav"
    _description = "Connection to an webdav server"

    webdav_hostname = fields.Char("Hostname", tracking=True)
    webdav_login = fields.Char("Webdav Login Name", tracking=True)
    webdav_password = fields.Char("Webdav Password")
    use_proxy = fields.Boolean("Use Proxy", tracking=True)
    proxy_hostname = fields.Char("Proxy Hostname", tracking=True)
    proxy_login = fields.Char("Proxy Login Name", tracking=True)
    proxy_password = fields.Char("Proxy Password")
    use_ssl = fields.Boolean("Use SSL", tracking=True)
    cert_path = fields.Char("Certificate Path", tracking=True)
    key_path = fields.Char("Key Path", tracking=True)
    recv_speed = fields.Integer(
        "Receive Speed",
        default=3000000,
        help="Download Rate in Bytes per Second",
        tracking=True,
    )
    send_speed = fields.Integer(
        default=3000000,
        help="Upload Rate in Bytes per Second",
        tracking=True,
    )
    verbose = fields.Boolean(
        tracking=True,
    )
    disable_check = fields.Boolean(
        default=False,
        tracking=True,
    )
    chunk_size = fields.Integer(
        default=65536,
        tracking=True,
    )

    def connect(self):
        options = {
            "webdav_hostname": self.webdav_hostname,
            "webdav_login": self.webdav_login,
            "webdav_password": self.webdav_password,
            "recv_speed": self.recv_speed,
            "send_speed": self.send_speed,
            "verbose": self.verbose,
            "disable_check": self.disable_check,
            "chunk_size": self.chunk_size,
        }
        if self.use_proxy:
            options["proxy_hostname"] = self.proxy_hostname
            options["proxy_login"] = self.proxy_login
            options["proxy_password"] = self.proxy_password
        if self.use_ssl:
            options["cert_path"] = self.cert_path
            options["key_path"] = self.key_path

        client = Client(options)
        return client
