# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import base64
import json
from odoo.tests.common import Form
from odoo.addons.zbsync.tests.test_common import ZBSPipelineCase
from odoo.tests import Form


class TestXML(ZBSPipelineCase):
    def test_xml2dict(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f1": "v1"}])},
        )

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync_xml.model_zbs_transformer_xml"),
            {"ttype": "dict2xml"},
        )
        line.keep_input_filter = False
        instance = pipeline.start({})
        instance._complete_run()
        data = instance._eval_data()
        value = data[0].content.replace("\t", "").replace("\n", "")
        self.assertEqual(
            value,
            """<?xml version="1.0" encoding=\"utf-8\"?><data><f1>v1</f1></data>""",
        )

    def test_xml2dict_records(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"record": [{"f1": "v1"}, {"f1": "v1"}]}])},
        )

        code = "data[0]"

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync_xml.model_zbs_transformer_xml"),
            {"ttype": "dict2xml"},
        )
        line.keep_input_filter = False
        instance = pipeline.start({})
        instance._complete_run()
        data = instance._eval_data()
        value = data[0].content.replace("\t", "").replace("\n", "")
        self.assertEqual(
            value,
            """<?xml version="1.0" encoding=\"utf-8\"?><data><record><f1>v1</f1></record><record><f1>v1</f1></record></data>""",
        )

    def test_dict2xmlb64(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f1": "v1"}])},
        )

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync_xml.model_zbs_transformer_xml"),
            {"ttype": "dict2xmlb64"},
        )
        line.keep_input_filter = False
        instance = pipeline.start({})
        instance._complete_run()
        data = instance._eval_data()
        value = base64.b64decode(data[0].content.decode("utf-8")).decode("utf8")
        value = value.replace("\t", "").replace("\n", "")
        self.assertEqual(
            value,
            """<?xml version="1.0" encoding=\"utf-8\"?><data><f1>v1</f1></data>""",
        )

    def test_leave_out_root_element_name_and_just_output_data(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "keep input filter"
        pipeline = form.save()

        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {"data": json.dumps([{"f1": "v1"}])},
        )

        worker, line = self.add_line(
            pipeline,
            self.env.ref("zbsync_xml.model_zbs_transformer_xml"),
            {"ttype": "dict2xml"},
        )
        worker.root_element_name = ""
        line.keep_input_filter = False
        instance = pipeline.start({})
        instance._complete_run()
        data = instance._eval_data()
        value = data[0].content.replace("\t", "").replace("\n", "")
        self.assertEqual(
            value,
            """<f1>v1</f1>""",
        )
