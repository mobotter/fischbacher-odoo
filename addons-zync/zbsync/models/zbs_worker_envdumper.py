# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class InstanceEnvDumper(models.Model):
    _inherit = "zbs.worker"
    _name = "zbs.instance.env.dumper"
    _description = "Zync Instance Env Dumper"

    line_ids = fields.One2many(
        "zbs.instance.env.dumper.line", "env_dumper_id", string="Lines", copy=True
    )

    def process(self, instance, data, errors=None):
        globals = self.env.context["zbs_instance_env"]._d
        globals["data"] = data
        for line in self.line_ids:
            value = self.env["zbs.tools"]._exec_get_result(line.code, globals)
            self.env.context["zbs_instance_env"][line.key] = value
        return instance.Result(data)


class InstanceEnvDumperLine(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.instance.env.dumper.line"
    _description = "Zync Environment Dumper Line"

    env_dumper_id = fields.Many2one("zbs.instance.env.dumper")
    key = fields.Char("Key")
    code = fields.Char("Code")
