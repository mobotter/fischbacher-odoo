# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class ImportExcel(models.Model):
    _inherit = "zbsync.base_wizard"
    _name = "zbsync.wiz.import_excel"
    _description = "Import Excel Wizard"

    def fill_pipeline(self, pipeline):
        worker = self.env["zbs.grabber.csvexcel"].create(
            {
                "name": "-",
            }
        )
        pipeline._add_worker(worker)
