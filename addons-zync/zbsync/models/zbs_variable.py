# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, fields, models


class Variable(models.Model):
    _name = "zbs.variable"
    _description = "Variables, that can be used in environments"

    name = fields.Char("Name", required=True)
    ttype = fields.Selection(
        [
            ("string", "String"),
            ("int", "Integer"),
            ("float", "Float"),
            ("bool", "Boolean"),
        ],
        string="Type",
        default="string",
        required=True,
    )

    @api.model
    def _get_values(self, zenv):
        vars = self.sudo().search([])
        values = self.env["zbs.variable.value"].search(
            [("environment_ids", "=", zenv.id)],
        )
        result = {}
        for var in vars:
            value = values.filtered(lambda x: x.variable_id == var)
            if len(value) >= 1:
                value = value[0].name
                value = var._convert(value)
                result[var.name] = value
        result = self.env["zbs.tools"].zebrooset(result)
        return result

    def _convert(self, value):
        self.ensure_one()
        if self.ttype == "int":
            return int(value)
        elif self.ttype == "float":
            return float(value)
        elif self.ttype == "bool":
            return bool(value)
        else:
            return str(value)
