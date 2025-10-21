# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import odoo
import json
from odoo.tests.common import Form
from odoo.tests.common import Form
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase
from .. import URL


class TestReceiver(ZBSPipelineCase, odoo.tests.HttpCase):
    def test_receiver(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter"
        pipeline = form.save()
        pipeline.line_ids[-1].worker_id.return_data = False

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f1": "v1"}])},
        )
        line.continue_immediately = True

        code = "data[0]"

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_transformer_python"),
            {"code": code},
        )
        line.continue_immediately = True
        line.keep_input_filter = False

        start_worker = pipeline.line_ids.sorted()[0].worker_id
        start_worker.identifier = "get_something"
        identifier = start_worker.identifier

        response = self.url_open(
            url=URL + "testing/" + identifier,
            data=json.dumps({"some": "data"}),
            headers={
                "Content-Type": "application/json",
                # "Accept": "application/json",
            },
            timeout=600,
        )
        self.assertEqual(response.status_code, 200)
        answer = json.loads(response.text)
        self.assertEqual(answer, [])

        # return some data
        pipeline.line_ids.sorted()[-1].worker_id.return_data = True
        response = self.url_open(
            url=URL + "testing/" + identifier,
            data={"some": "data"},
            timeout=600,
        )
        self.assertEqual(response.status_code, 200)
        answer = json.loads(response.text)
        self.assertEqual(answer, [{"f1": "v1"}])

    def test_receiver_if_returns_error(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter"
        pipeline = form.save()
        pipeline.line_ids[-1].worker_id.return_data = False

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_transformer_python"),
            {"code": "raise Exception('error!')"},
        )
        line.continue_immediately = True

        start_worker = pipeline.line_ids.sorted()[0].worker_id
        start_worker.identifier = "get_something"
        identifier = start_worker.identifier

        response = self.url_open(
            url=URL + "testing/" + identifier,
            data=json.dumps({"some": "data"}),
            headers={
                "Content-Type": "application/json",
                # "Accept": "application/json",
            },
            timeout=600,
        )
        self.assertEqual(response.status_code, 500)
