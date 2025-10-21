# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models
from .expression import WhereExpression


class Domain(models.Model):
    _inherit = ["zbs.domain"]
    _name = "zbs.domain.sql"
    _description = "SQL Domain"

    parent_id = fields.Many2one("zbs.grabber.sql")


class SqlGrabber(models.Model):
    _inherit = ["zbs.grabber", "zbs.sql.connection.mixin", "zbs.domains.mixin"]
    _name = "zbs.grabber.sql"
    _description = "SQL Grabber"

    domain_ids = fields.One2many("zbs.domain.sql")
    sql = fields.Text("SQL")

    def process(self, instance, data, errors=None):
        result_records = []
        with self.connection_id._get_conn() as remote_cr:
            for index, record in self.env["zebrooset"].iterate(data):
                domain = self.resolve_domain(instance, data=data, record=record) or []
                sql = self.sql
                if not domain:
                    whereclause = "1=1"
                    whereparams = tuple([])
                else:
                    whereclause, whereparams = WhereExpression(
                        domain, self.connection_id.type
                    ).get_clause()
                if "{where}" in sql:
                    sql = sql.replace("{where}", whereclause)
                else:
                    whereparams = tuple([])

                records = self.connection_id.fetchall(remote_cr, sql, whereparams)
                self._apply_keep_input(index, record, data, records)

                result_records += records

        return instance.Result(result_records)
