# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models


class SnowflakeGrabber(models.Model):
    _inherit = ["zbs.grabber"]
    _name = "zbs.grabber.snowflake"
    _description = "Snowflake Grabber"

    sql = fields.Text("SQL")
    connection_id = fields.Many2one("zbs.connection.snowflake")

    def process(self, instance, data, errors=None):
        result_records = []
        for index, record in self.env["zebrooset"].iterate(data):
            sql = self.sql
            records = self.connection_id.fetchall(sql)
            self._apply_keep_input(index, record, data, records)

            result_records += records

        return instance.Result(result_records)
