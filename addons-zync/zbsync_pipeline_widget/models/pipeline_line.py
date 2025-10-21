# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class PipelineLine(models.Model):
    _inherit = "zbs.pipeline.line"

    def compute_rendercontent(self):
        self.ensure_one()
        res = {
            "line": {
                "id": self.id,
                "enabled": self.enabled,
                "model": self._name,
                "batchsize": self.batchsize,
                "abort_on_error": self.abort_on_error,
                "continue_immediately": self.continue_immediately,
                "keep_input_filter": self.keep_input_filter,
                "range": self.range,
                "output_range": self.output_range,
                "ffilter": self.ffilter,
                "output_ffilter": self.output_ffilter,
                "path_content": self.path_content,
                "retry_pattern": self.retry_pattern,
            },
            "worker": self.worker_id.compute_rendercontent(),
        }
        return res
