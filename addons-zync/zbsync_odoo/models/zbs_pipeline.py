# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import _, api, fields, models, SUPERUSER_ID
import json
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from .. import odoorpc
from odoo.addons.zbsync.models.zebrooset import ZebrooSet
import pickle


class PipelineLine(models.Model):
    _inherit = "zbs.pipeline.line"

    @api.model
    def dump_data(self, data):
        if isinstance(data, odoorpc.models.Model):
            connection_id = data.env._zbsync_odoo_connection
            data = {
                "model": data._name,
                "ids": data.ids,
                "connection_id": connection_id,
            }
            return "odoorpc:" + json.dumps(data)

        res = super().dump_data(data)
        return res

    @api.model
    def load_data(self, data):
        if isinstance(data, str) and data.startswith("odoorpc:"):
            data = json.loads(data[8:])
            conn = self.env["zbs.connection.odoo"].browse(data["connection_id"])
            instance = conn._get_obj(data["model"])
            instance = instance.browse(data["ids"])
            setattr(instance.env, "_zbsync_odoo_connection", conn.id)
            return instance

        res = super().load_data(data)
        return res
