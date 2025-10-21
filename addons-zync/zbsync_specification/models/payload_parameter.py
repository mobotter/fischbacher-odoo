# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models, fields, api
from odoo.exceptions import UserError


class PayloadParameter(models.Model):
    _name = "zbs.payload.parameter"
    _description = "Zync API Payload Parameter"

    name = fields.Char("Name", compute="_compute_name", store=True)
    field = fields.Char("Field")
    config_id = fields.Many2one("zbs.rest.config", "Config")
    example = fields.Char("Example Value")
    parameter_type = fields.Selection(
        [("path", "path"), ("query", "query"), ("header", "header")]
    )
    required = fields.Boolean("Required", default=False)
    description = fields.Char("Description")
    allow_reserved = fields.Boolean("Allow Reserved")
    property_type_id = fields.Many2one("zbs.value.property.type", "Property Type")

    @api.constrains("start_id", "parameter_type")
    def _check_unique_start_path(self):
        for rec in self:
            if (
                len(
                    self.search(
                        [
                            ("config_id", "=", self.config_id.id),
                            ("parameter_type", "=", "path"),
                        ]
                    )
                )
                > 1
            ):
                raise UserError("No more then one Path Variable per Start allowed")

    @api.depends("field", "parameter_type")
    def _compute_name(self):
        for rec in self:
            if rec.parameter_type == "path":
                rec.name = "<" + rec.field + ">"
            elif rec.parameter_type == "query":
                rec.name = "?{}=value".format(rec.field)
            elif rec.parameter_type == "header":
                rec.name = "Header: {}".format(rec.field)
            else:
                rec.name = "NOT YET IMPLEMENTED"

    def generate_api_spec(self):
        parameter = {}
        parameter["in"] = self.parameter_type
        parameter["description"] = self.description
        parameter["example"] = self.example
        parameter["name"] = self.field
        parameter["required"] = self.required
        parameter["schema"] = {}
        parameter["schema"]["type"] = self.property_type_id.name
        if self.property_type_id.format:
            parameter["schema"]["format"] = self.property_type_id.format
        return parameter
