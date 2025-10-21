# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
from odoo.tests import Form
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase


class Unittest(ZBSPipelineCase):

    @classmethod
    def setUpClass(cls):
        # otherwise request does not work
        cls.test_tags.remove("standard")
        super().setUpClass()

    def test_webworker_(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "Webworker"
        pipeline = form.save()

        model = self.env.ref("zbsync.model_zbs_const")
        _, pipeline_line = self.add_line(
            pipeline, model, {"data": json.dumps({"intA": 100, "intB": 200})}
        )
        url = self.env["zbs.web.url"].create(
            {
                "name": "http://www.dneonline.com",
            }
        )
        pipeline_line.path_content = "data"
        model = self.env.ref("zbsync_web.model_zbs_web_worker")
        webworker, _ = self.add_line(
            pipeline,
            model,
            {
                "url_id": url.id,
                "path": "/calculator.asmx",
                "method": "get",
                "request_content_type": "text/html",
                "response_content_type": "html",
            },
        )

        instance = pipeline.run_test()._complete_run()
        test = instance._eval_data()
        self.assertIn("<html>", test[0])
