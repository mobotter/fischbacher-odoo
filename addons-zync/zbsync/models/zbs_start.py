# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import api, fields, models


class ZBSStart(models.Model):
    _inherit = "zbs.worker"
    _name = "zbs.start"
    _description = "Start your Pipeline"

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if not rec.name:
                rec.name = "-"
        return res

    def is_start(self):
        return True

    def process(self, instance, data, errors=None):
        from .zebrooset import ZebrooSet

        instance.date_start = fields.Datetime.now()

        data = instance.initial_data or None
        data = instance.line_ids.load_data(data)
        if isinstance(data, ZebrooSet):
            data._wraplist()

        # get last execution date
        domain = [
            ("pipeline_id", "=", instance.pipeline_id.id),
            ("origin", "=", instance.origin),
            ("id", "<", instance.id),
            ("environment_id", "=", instance.environment_id.id),
        ]
        prev_instance = instance.search(domain, limit=1, order="id desc")
        if prev_instance:
            last_execution_date = prev_instance.date_start
        else:
            last_execution_date = fields.Datetime.from_string("1980-04-04 00:00:00")
        instance_env = self.env.context["zbs_instance_env"]
        instance_env["last_execution_date"] = last_execution_date
        instance._set_state("running")
        return instance.Result(data)
