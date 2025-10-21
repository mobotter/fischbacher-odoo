# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class ZBSStringBuilder(models.Model):
    _inherit = "zbs.worker"
    _name = "zbs.string_builder"
    _description = "Text/String Builder"

    # static
    header = fields.Text("Header")
    footer = fields.Text("Footer")

    separator = fields.Text("Separator", default="\n")

    def _extract_content(self, record):
        if isinstance(record, str):
            return record
        return record.content

    def process(self, instance, data, errors=None):
        SEP = self.separator

        result = self._eval_expression(
            self.header,
            0,
            data,
            data,
            input=self.env.context.get("zbs_prepared_input_data"),
        )
        for index, rec in data._iterate_records():
            result += SEP + self._extract_content(rec)

        if self.footer:
            footer = self._eval_expression(
                self.footer,
                0,
                data,
                data,
                input=self.env.context.get("zbs_prepared_input_data"),
            )
            result += SEP + footer

        return instance.Result(result)
