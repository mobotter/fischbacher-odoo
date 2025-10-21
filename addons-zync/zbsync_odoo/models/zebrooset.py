# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from .. import odoorpc
from .odoorpc_wrapper import RPCWrapper
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class ZebrooSet(models.AbstractModel):
    _inherit = "zebrooset"

    def _encode(self, obj, just_test=False):
        try:
            return super()._encode(obj, just_test=just_test)
        except NotImplementedError:
            if isinstance(obj, RPCWrapper):
                return {
                    "_type": "RPCWrapper",
                    "ids": obj.ids,
                    "model": obj.obj._name,
                    "connection_id": obj.connection,
                }
            if isinstance(obj, odoorpc.models.Model):
                return {
                    "_type": "odoorpc.models.Model",
                    "ids": obj.ids,
                    "model": obj._name,
                    "connection_id": getattr(obj, "_zbsync_odoo_connection"),
                }
            else:
                raise

    def _decode(self, obj, just_test=False):
        try:
            return super()._decode(obj, just_test=just_test)
        except NotImplementedError:
            if obj["_type"] in ["odoorpc.models.Model", "RPCWrapper"]:
                conn = self.env["zbs.connection.odoo"].browse(obj["connection_id"])
                ids = obj["ids"]
                obj = conn._get_obj(obj["model"])
                result = RPCWrapper(conn.id, obj, ids)
                return result
            else:
                raise
