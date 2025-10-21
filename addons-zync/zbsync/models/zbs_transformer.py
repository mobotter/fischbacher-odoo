# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class Transformer(models.AbstractModel):
    _inherit = "zbs.worker"
    _name = "zbs.transformer"
    _description = "Transformer"

    propagate_code_result = fields.Boolean(
        "Do not aggregate step results",
        help="If set, then you must return the total result for all incoming batches.",
        tracking=True,
    )

    def process(self, instance, data, errors=None):
        if self.propagate_code_result:
            result = self._do_exec(data, data, 0, instance, errors=errors)
            return instance.Result(result)
        return super().process(instance, data, errors=errors)

    def process_record(self, instance, index, record, data, errors=None):
        return self._do_exec(record, data, index, instance, errors=errors)


class PythonTransformer(models.Model):
    _inherit = "zbs.transformer"
    _name = "zbs.transformer.python"
    _description = "Python Code Worker"

    code = fields.Text("Code", tracking=True)

    def _do_exec(self, record, data, index, instance, errors):
        return self.env["zbs.tools"]._exec_get_result(
            self.code,
            {
                "data": data,
                "record": record,
                "index": index,
                "instance": instance,
                "errors": errors,
            },
        )

    def process_record(self, instance, index, record, data, errors=None):
        return self._do_exec(record, data, index, instance, errors=errors)
