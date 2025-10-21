# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class ZbsReceiveAuthorizer(models.Model):
    _inherit = ["mail.thread", "zbs.xport.mixin"]
    _name = "zbs.receive.authorizer"
    _description = "Authorizer for Receving Webcalls"
    _order = "priority desc"

    priority = fields.Integer("Priority", default=10)
    name = fields.Char("Name")
    code = fields.Text("Code", tracking=True)
    auth_type = fields.Selection(
        [("code", "Code")], string="Type", required=True, default="code"
    )

    def authorize_webrequest(self, headers, postdata, keyvalues):
        self.ensure_one()
        default_user = self.env.ref("base.public_user")
        default = {"odoo_user_id": default_user.id}
        if self.auth_type == "code":
            auth_result = self.env["zbs.tools"]._exec_get_result(
                self.code,
                {
                    "headers": headers,
                    "postdata": postdata,
                    "keyvalues": keyvalues,
                },
            )
            if auth_result:
                if "odoo_user_id" in auth_result:
                    default["odoo_user_id"] = auth_result["odoo_user_id"]
                return {"authorized": True, "method": "custom_code", "payload": default}
