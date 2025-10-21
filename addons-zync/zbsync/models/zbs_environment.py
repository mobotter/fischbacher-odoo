# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Environment(models.Model):
    _name = "zbs.environment"
    _description = "Zync Environment"

    name = fields.Char("Name", required=True)
    is_default = fields.Boolean("Is Default", default=False)
    variable_value_ids = fields.Many2many(
        "zbs.variable.value", string="Variable Values"
    )

    @api.model
    def _get_default_env(self):
        envs = self.sudo().search([])
        if len(envs) == 1:
            return envs
        envs = envs.filtered(lambda x: x.is_default)
        if len(envs) > 1:
            raise UserError(_("Multiple default environments found"))
        return envs and envs[0]

    @api.model
    def _export(self):
        result = {}
        values = self.env["zbs.variable.value"].search(
            [("environment_ids", "in", self.ids)]
        )
        for var in values.variable_id:
            var_values = values.filtered(lambda x: x.variable_id == var)
            result[var.name] = []
            for value in var_values:
                v = {
                    "value": value.name,
                    "environments": value.environment_ids.mapped("name"),
                }
                result[var.name].append(v)
        return result

    @api.model
    def _import(self, data):
        for varname, values in data.items():
            var = self.env["zbs.variable"].search([("name", "=", varname)], limit=1)
            if not var:
                var = self.env["zbs.variable"].create({"name": varname})
            self.env["zbs.variable.value"].search(
                [("variable_id", "=", var.id)]
            ).unlink()
            for value in values or []:
                dbenvs = self.env["zbs.environment"]
                for envname in value["environments"]:
                    if envname not in dbenvs.mapped("name"):
                        dbenvs |= self.env["zbs.environment"].create({"name": envname})
                self.env["zbs.variable.value"].create(
                    {
                        "variable_id": var.id,
                        "name": value["value"],
                        "environment_ids": [
                            (
                                6,
                                0,
                                dbenvs.filtered(
                                    lambda x: x.name in value["environments"]
                                ).ids,
                            )
                        ],
                    }
                )

    @api.model
    # TODO documentation
    def _extract_company(self, environment):
        if "company_id" in environment.keys():
            comp = self.env["res.company"].sudo().browse(int(environment["company_id"]))
            return comp
