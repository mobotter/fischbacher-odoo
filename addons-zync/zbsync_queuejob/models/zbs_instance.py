# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, models
from odoo.addons.zbsync.exceptions import RetryableJobError


class Instance(models.Model):
    _inherit = "zbs.instance"

    @api.model
    def _is_using_queuejobs(self):
        return True

    def _get_default_objects(self, defaults):
        res = super()._get_default_objects(defaults)
        res["RetryableJobError"] = RetryableJobError
        return res

    def _precheck_can_cron_heartbeat(self):
        res = super()._precheck_can_cron_heartbeat()
        if not res:
            return res

        check = self.env["ir.config_parameter"].get_param(
            key="zbs.check.duplicate_queue_jobs", default=False
        )
        if check in ["0", "false", "False"]:
            return True

        if self.env["queue.job"].search_count(
            [
                ("identity_key", "=", self.identity_key),
                ("state", "not in", ["done", "failed", "cancel", "cancelled"]),
            ]
        ):
            # case at customer: queuejobs were created with same identity keys
            # really avoid that
            return False

        return True
