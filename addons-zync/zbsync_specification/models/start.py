# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, fields, models


# sample instance_env
{
    "web_request": {
        "path": "/1/?field=value",
        "request_method": "GET",
        "request_type": "application/json",
    },
    # search
    "domain": [],  # evaluierte domaene rauskommend aus config eval
    # instance_env.domain
    # instance_env.domain
    # post (upsert)
    "params": {
        "field": "value",
        "field2": "value2",
    },
}


class StartElement(models.Model):
    _inherit = "zbs.start"

    description = fields.Char("Description")
    rest_config_id = fields.Many2one("zbs.rest.config", string="API Config")
    request_method = fields.Selection(
        compute="_get_request_method",
        inverse="_set_request_method",
        string="Request Method",
        store=True,
    )
    request_method_manual = fields.Selection(
        [("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("DELETE", "DELETE")],
        string="Request Method Manual",
    )
    request_type = fields.Selection(
        compute="_get_request_type",
        inverse="_set_request_type",
        string="HTTP Request Type",
    )
    request_type_manual = fields.Selection(
        [
            ("application/json", "application/json"),
            ("application/text", "application/text"),
        ],
        string="Payload Type Manual",
    )

    @api.depends(
        "rest_config_id", "rest_config_id.request_method", "request_method_manual"
    )
    def _get_request_method(self):
        self.request_method = (
            self.rest_config_id.request_method
            if self.rest_config_id
            else self.request_method_manual
        )
        return False

    def _set_request_method(self):
        self.request_method_manual = self.request_method

    @api.depends("rest_config_id")
    def _get_request_type(self):
        self.request_type = (
            self.rest_config_id.request_type
            if self.rest_config_id
            else self.request_type_manual
        )
        return False

    def _set_request_type(self):
        self.request_type_manual = self.request_type

    def process(self, instance, data, errors=None):
        if self.rest_config_id and data:
            self._check_payload_data(data)
        res = super().process(instance, data, errors=errors)

        instance_env = self.env.context["zbs_instance_env"]
        if self.rest_config_id:
            if "path_parameter" in instance_env:
                instance_env[
                    "domain"
                ] = self.rest_config_id.sudo().create_parameter_domain(
                    "path", instance_env["path_parameter"]
                )

        return res

    def _check_payload_data(self, data):
        self.rest_config_id._check_payload_data(data)
