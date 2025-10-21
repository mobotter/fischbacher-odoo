# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class InstanceItem(models.Model):
    _inherit = "of.instance.item"

    def _on_has_cursor_changed(self):
        if not self.has_cursor:
            return
        metadata = self.restore_metadata()
        if metadata.get("instance_id"):
            zbinstance = self.env["zbs.instance"].sudo().browse(metadata["instance_id"])
            if zbinstance.state in ["success", "failed"]:
                metadata.pop("instance_id")
                self.store_metadata(metadata)

    def _fetch_additional_data_for_heartbeat(self):
        res = super()._fetch_additional_data_for_heartbeat()
        previous_data = self.item_id.incoming_ids._zbs_get_previous_data(self)
        res["zync"] = previous_data
        return res
