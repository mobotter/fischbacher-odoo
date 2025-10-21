# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, models
from odoo.addons.zbsync.exceptions import RetryableJobError


class Tools(models.AbstractModel):
    _inherit = "zbs.tools"

    @api.model
    def _queuejob_idkey_exists(self, identity_key):
        self.env.cr.execute(
            "select id from queue_job where identity_key=%s and state in ('wait_dependencies', 'pending', 'started', 'enqueued')",
            (identity_key,),
        )
        return bool(self.env.cr.fetchone())

    @api.model
    def with_delay(self, instance, enabled, *args, **kwargs):
        if enabled and not self.env["zbs.tools"]._is_testing():
            idkey = kwargs.get("identity_key")
            if idkey:
                if self._queuejob_idkey_exists(idkey):
                    raise RetryableJobError(
                        f"A job with the same identity key already exists: {idkey}"
                    )
            return instance.with_delay(*args, **kwargs)
        else:
            return instance
