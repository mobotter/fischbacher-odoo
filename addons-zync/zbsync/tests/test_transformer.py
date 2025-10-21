# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
import time
from odoo import fields
from odoo.tests import Form
from .test_pipe import ZBSPipelineCase


class TestTransformer(ZBSPipelineCase):
    def test_transformer(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f1": "v1"}])},
        )

        code = "data[0]"

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_transformer_python"),
            {"code": code},
        )
        line.keep_input_filter = False
        instance = pipeline.start({})
        instance.heartbeat()
        instance.heartbeat()
        data = instance._eval_data()
        self.assertTrue(data._is_equal([{"f1": "v1"}]))

    def test_last_execution_date(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps({"f1": "v1"})},
        )

        code = "123"

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_transformer_python"),
            {"code": code, "propagate_code_result": True},
        )

        instance = pipeline.start({})
        instance.heartbeat()
        instance.heartbeat()
        d1 = fields.Datetime.from_string("1980-04-04 01:02:03")
        instance.date_start = d1
        # unittest has different environment like real system
        instance.env["zbs.instance"].browse(instance.ids).date_start = d1

        instance = pipeline.start({})
        instance.heartbeat()
        instance.heartbeat()
        time.sleep(1)
        self.assertEqual(instance._get_env(), {"last_execution_date": d1})

    def test_variables(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "test variables"
        pipeline = form.save()

        # environments
        self.env["zbs.environment"].search([]).write({"is_default": False})
        env = self.env["zbs.environment"].create({"name": "test", "is_default": True})
        var1 = self.env["zbs.variable"].create({"name": "var1"})
        value1 = self.env["zbs.variable.value"].create(
            {"variable_id": var1.id, "environment_ids": [env.id], "name": "value1"}
        )

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps({"f1": "v1"})},
        )

        code = "assert vars.var1 == 'value1'\n1"

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_transformer_python"),
            {"code": code, "propagate_code_result": True},
        )

        instance = pipeline.start({})
        instance.heartbeat()
        instance.heartbeat()
        d1 = fields.Datetime.from_string("1980-04-04 01:02:03")
        instance.date_start = d1

        instance = pipeline.start({})
        instance._complete_run()
