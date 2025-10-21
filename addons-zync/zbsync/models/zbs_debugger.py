# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

# used to watch the intermediate results
from odoo import models
import logging


class ZBSDebugger(models.Model):
    _inherit = "zbs.worker"
    _name = "zbs.debugger"
    _description = "debug"

    def process(self, instance, data, errors=None):
        logger = logging.getLogger(f"zbs.debugger")
        for record in self.env["zebrooset"].iterate(data):
            logger.info(str(record))
        return instance.Result(data)
