# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class VariableValue(models.Model):
    _name = "zbs.variable.value"
    _order = "variable_name, name"
    _description = "Zync Variable Value"

    variable_id = fields.Many2one("zbs.variable", "Variable", required=True)
    variable_name = fields.Char(
        related="variable_id.name", string="Variable Name", store=True
    )
    environment_ids = fields.Many2many(
        "zbs.environment", string="Environment", required=True
    )
    name = fields.Char("Value")
