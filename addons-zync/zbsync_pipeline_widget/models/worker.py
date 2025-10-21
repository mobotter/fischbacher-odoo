# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class Worker(models.AbstractModel):
    _inherit = "zbs.worker"

    def compute_rendercontent(self):
        self.ensure_one()
        return {
            "id": self.id,
            "model": self._name,
            "model_description": getattr(self, "_description", self._name)
            or self._name,
            "name": self.name,
            "can_open_worker_detail": self.can_open_worker_detail,
            "comment": self.comment,
        }
