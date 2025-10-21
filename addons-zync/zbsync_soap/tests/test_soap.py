# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
from odoo.tests.common import Form
from odoo.tests import Form
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase


class SoapTest(ZBSPipelineCase):

    @classmethod
    def setUpClass(cls):
        # otherwise request does not work
        cls.test_tags.remove("standard")
        super().setUpClass()

    def test_soap(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "Soap-Test"
        pipeline = form.save()

        model = self.env.ref("zbsync.model_zbs_const")
        _, pipeline_line = self.add_line(
            pipeline, model, {"data": json.dumps({"intA": 100, "intB": 200})}
        )
        pipeline_line.path_content = "data"
        model = self.env.ref("zbsync_soap.model_zbs_grabber_soap")
        soap_grabber, _ = self.add_line(
            pipeline, model, {"function_call": "Add(**record)"}
        )

        soap_grabber.connection_id = self.env["zbs.connection.soap"].create(
            {"wsdl_url": "http://www.dneonline.com/calculator.asmx?wsdl"}
        )
        instance = pipeline.run_test()
        instance._complete_run()
        test = instance._eval_data()
        self.assertEqual(test[0].soap, 300)
