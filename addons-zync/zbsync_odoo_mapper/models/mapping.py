# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo.addons.zbsync_odoo import odoorpc
from odoo import api, models


class Mapping(models.Model):
    _inherit = "zbs.mapping"

    def _is_list(self, obj):
        res = super()._is_list(obj)
        if isinstance(obj, odoorpc.models.Model):
            return True
        return res

    @api.model
    def _condition_to_return_ints(self):
        if self.action in ["direct", "lookup"]:
            return True
        return False

    @api.model
    def _get_source_value(self, record, field):
        res = super()._get_source_value(record, field)
        if isinstance(res, (models.Model, odoorpc.models.Model)):
            is_m2o = None
            if isinstance(record, models.Model):
                if field in record._fields:
                    if record._fields[field].type == "many2one":
                        is_m2o = True
            elif isinstance(record, odoorpc.models.Model):
                try:
                    conn = self.env["zbs.connection.odoo"].browse(
                        record._zbs_connection
                    )
                except AttributeError:
                    conn = self.env["zbs.connection.odoo"].browse(
                        record.env.context["_zbs_connection"]
                    )
                model_fields = conn._get_fields_of_obj(record._name)
                field = model_fields[field]
                if field:
                    if field["type"] == "many2one":
                        is_m2o = True
            # TODO check this code
            # cannot distinguish x2many and many2one
            if is_m2o:
                if self._condition_to_return_ints():
                    return res.ids and res.ids[0] or False
            if self._condition_to_return_ints():
                res = res.ids
        return res
