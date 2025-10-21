# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
from odoo.tests.common import Form
from odoo.tests.common import Form
from odoo.tools.safe_eval import safe_eval
from .test_common import ZBSPipelineCase
from ..exceptions import BatchFailed

try:
    from odoo.tools.safe_eval import wrap_module
except:
    from odoo.tools import wrap_module


class ZBSPipelineCaseCommonTests(ZBSPipelineCase):
    def test_make_pipe(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "Hansi"
        pipeline = form.save()

        self.assertEqual(len(pipeline.line_ids), 2)

    def test_keep_input_filter(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps({"f1": "v1"})},
        )

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps({"f2": "v2"})},
        )
        line.keep_input_filter = "{'f1': input.f1}"
        instance = pipeline.start({})
        instance._complete_run()
        test = instance._eval_data()
        self.assertTrue(test)
        instance.heartbeat()
        data = instance._eval_data()
        self.assertTrue(data._is_equal([{"f1": "v1", "f2": "v2"}]))

    def test_keep_input_filter_at_records(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter at records"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f1": "v1"}, {"f1": "v2"}])},
        )

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f2": "v1"}, {"f2": "v2"}])},
        )
        line.keep_input_filter = "{'f1': input[index].f1}"
        instance = pipeline.start({})
        instance.heartbeat()
        instance.heartbeat()
        test = instance._eval_data()
        self.assertTrue(test)
        instance.heartbeat()
        data = instance._eval_data()
        self.assertTrue(
            data._is_equal([{"f1": "v1", "f2": "v1"}, {"f1": "v2", "f2": "v2"}])
        )

    def test_domain_eval_arrow_lib(self):
        arrow2 = wrap_module(__import__("arrow"), ["get"])
        safe_eval("arrow.get()", {"arrow": arrow2})

    def test_if_condition_not(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter at records"
        pipeline = form.save()

        worker_const1, line_const1 = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f": "v1"}])},
        )

        worker_const2, line_const2 = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f": "v2"}])},
        )
        line_const2.condition = "input.f != 'v1'"

        instance = pipeline.start({})._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal([{"f": "v1"}]))

    def test_if_condition(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter at records"
        pipeline = form.save()

        worker_const1, line_const1 = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f": "v1"}])},
        )

        worker_const2, line_const2 = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f": "v2"}])},
        )
        line_const2.condition = "input.f == 'v1'"

        instance = pipeline.start({})._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal([{"f": "v2"}]))

    def test_batches(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "test_batches"
        pipeline = form.save()

        worker_const1, line_const1 = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f": "v1"}])},
        )

        instance = pipeline.start({})._complete_run()
        data = instance._eval_data()
        self.assertTrue(data._is_equal([{"f": "v1"}]))

    def test_exceptions(self):
        """
        raises exception if name is 'bad'
        """
        form = Form(self.env["zbs.pipeline"])
        form.name = "test_batches"
        pipeline = form.save()

        worker_const1, line_const1 = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"name": "good"}, {"name": "bad"}, {"name": "last"}])},
        )
        code = """if record.name == 'bad':
    raise Exception('bad found')
True
        """
        worker_transformer, line_transformer = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_transformer_python"),
            {"code": code},
        )

        instance = pipeline.start({})
        try:
            instance._complete_run()
        except BatchFailed:
            # self assertRaises did not work ... dont know why
            pass
        data = instance._eval_data()
        errors = instance._eval_exceptions()
        self.assertIn("bad found", str(errors))
        self.assertEqual(len(errors), 1, "Should be one bad guy")

        code = """if record.name == 'bad' or record.name == 'good':
    raise Exception('bad found')
True
        """
        try:
            instance = pipeline.start({})
            instance._complete_run()
        except BatchFailed:
            # self assertRaises did not work ... dont know why
            pass
        data = instance._eval_data()
        errors = instance._eval_exceptions()
        self.assertIn("bad found", str(errors))
        self.assertEqual(
            len(errors), 1, "Should be one bad and one good guy but we do one exception"
        )

    def test_exceptions_as_parameter_to_next_line(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "test_batches"
        pipeline = form.save()

        worker_const1, line_const1 = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"name": "good"}, {"name": "bad"}, {"name": "last"}])},
        )
        code = """
if record.name == 'bad':
    raise Exception('bad found')
True
        """
        worker_transformer, line_transformer = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_transformer_python"),
            {"code": code},
        )
        code = """
return errors
        """
        worker_transformer, line_transformer = self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_transformer_python"),
            {"code": code},
        )
        worker_transformer.propagate_code_result = True

        try:
            instance = pipeline.start({})
            instance._complete_run()
        except BatchFailed:
            pass
        errors = instance._eval_exceptions()
        self.assertEqual(len(errors), 1, "Should be one bad guy")
        record = self.env["zebrooset"].loads(errors.record)
        self.assertEqual(record.name, "bad")
