# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo.tests.common import TransactionCase, Form


class TestExcelCSV(TransactionCase):
    def setUp(self):
        super().setUp()

    def test_excel_csv_wizard(self):
        return
        form = Form(self.env["zbsync.wiz.import_excel"])
        form.save()
        pipeline = form.button_ok()
        form.fill_pipeline()
        self.assertTrue(
            pipeline.line_ids.filtered(
                lambda x: x.worker_id._name == "zbs.grabber.csvexcel"
            )
        )
