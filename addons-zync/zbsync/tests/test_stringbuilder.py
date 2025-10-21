# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
from odoo.tests import Form
from .test_pipe import ZBSPipelineCase


class TestStringBuilder(ZBSPipelineCase):
    def test_transformer(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "test string builder"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f1": "v1"}, {"f1": "v2"}])},
        )

        code = "[record.f1]"

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_transformer_python"),
            {"code": code},
        )
        line.batchsize = 1
        line.keep_input_filter = False

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_string_builder"),
        )
        worker.header = "return 'my head'"
        worker.footer = "return 'my foot'"
        instance = pipeline.start({})
        instance._complete_run()
        instance._raise_for_status()
        data = instance._eval_data()
        self.assertTrue(data._is_equal(["my head\nv1\nv2\nmy foot"]))
