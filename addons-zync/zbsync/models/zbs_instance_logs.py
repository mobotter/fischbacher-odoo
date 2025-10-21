# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import api, fields, models
import json


class InstanceLogs(models.Model):
    _order = "id desc"
    _name = "zbs.instance.logs"
    _description = "Zync Instance Logs"

    batch_id = fields.Many2one(
        "zbs.instance.line.batch", required=True, ondelete="cascade"
    )
    line_id = fields.Many2one("zbs.instance.line", related="batch_id.line_id")
    instance_id = fields.Many2one(
        "zbs.instance", related="batch_id.line_id.instance_id", store=True
    )

    date_start = fields.Datetime(
        "Date Start", required=True, default=fields.Datetime.now
    )
    date_stop = fields.Datetime("Date Stop", required=False)
    duration = fields.Integer("Duration [s]", compute="_compute_duration", store=True)
    log = fields.Text("Log")
    output_data = fields.Text("Output Data")
    formatted_output = fields.Text(
        "Output Formatted", compute="_compute_formatted_output"
    )
    last_exception = fields.Text("Exception")

    @api.depends("date_start", "date_stop")
    def _compute_duration(self):
        for rec in self:
            if rec.date_start and rec.date_stop:
                rec.duration = (rec.date_stop - rec.date_start).total_seconds()
            else:
                rec.duration = 0

    @api.model
    def _format_output(self, data):
        try:
            formatted = self.env["zbs.pipeline.line"].load_data(data)
        except Exception as ex:
            return False
        else:
            try:
                formatted = json.dumps(formatted, indent=4)
            except:
                formatted = str(formatted)
            return formatted

    def _compute_formatted_output(self):
        for rec in self:
            rec.formatted_output = rec._format_output(rec.output_data)
