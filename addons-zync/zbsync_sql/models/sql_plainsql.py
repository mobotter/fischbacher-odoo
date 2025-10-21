# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
"""
Expects key columns in [{'___keys': ....}]
"""
from odoo import fields, models
from odoo.exceptions import ValidationError
import logging

logger = logging.getLogger()


class SqlDumper(models.Model):
    _inherit = [
        "zbs.dumper",
        "zbs.sql.connection.mixin",
        "zbs.dumper.mixin.cu",
    ]
    _name = "zbs.plain.sql"
    _description = "Execute SQL"

    plain_sql = fields.Text("Plain SQL")
    execute_per_record = fields.Boolean(
        "Execute per Record",
        help="If true, then there is a record variable otherwise only input exists.",
    )
    fetchtype = fields.Selection(
        [
            ("fetchall", "Fetch All"),
            ("fetchnone", "No Fetch"),
        ]
    )

    def _compute_capas(self):
        for rec in self:
            rec.can_keys = False
            rec.can_keys_multi_ok = False
            rec.can_delete_one2many = False
            rec.can_compare_delta = False

    def process(self, instance, data, errors=None):
        self = self.with_context(instance=instance)
        if not self.fetchtype:
            raise ValidationError("Please define fetch-type")

        def store_kept(res, kept):
            if self.fetchtype == "fetchnone":
                res = kept
            else:
                res = {
                    "data": res,
                    "kept": kept,
                }
            return res

        result = []
        zs_data = (
            self.env["zebrooset"].rs(data) if isinstance(data, (dict, list)) else input
        )
        with self.connection_id._get_conn() as cr:
            with self.connection_id._in_transaction(cr, "plain-sql-#{self.id}") as cr:
                if self.fetchtype == "fetchnone":
                    method = self.connection_id.execute
                elif self.fetchtype == "fetchall":
                    method = self.connection_id.fetchall

                params = {
                    "data": zs_data,
                    "input": zs_data,
                }

                if self.execute_per_record:
                    for i, record in enumerate(data._iterate_records()):
                        params["record"] = record
                        sql = self.env["zbs.tools"]._exec_get_result(
                            self.plain_sql, params
                        )
                        res = method(cr, sql, tuple([]))
                        kept = self._keep_input(i, record, zs_data)

                        res = store_kept(record, kept)
                        result.append(res)

                else:
                    method(cr, self.plain_sql, params)
                    sql = self.env["zbs.tools"]._exec_get_result(self.plain_sql, params)
                    res = getattr(self.connection_id, method)(cr, sql, tuple([]))
                    kept = self._keep_input(0, zs_data, zs_data)
                    res = store_kept(data, kept)
                    result.append(res)

        return instance.Result(result)
