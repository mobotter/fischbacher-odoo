# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
import uuid
from odoo.tests.common import Form
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase
from pathlib import Path


class FileDumper(ZBSPipelineCase):
    def test_file_dumper(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "File Dumper"
        pipeline = form.save()
        guid = str(uuid.uuid4())
        path = Path(f"/tmp/{guid}")
        self.add_line(
            pipeline,
            self.env.ref("zbsync.model_zbs_const"),
            {
                "data": json.dumps(
                    [
                        {
                            "name": "myname1",
                            "content": "anton",
                        },
                    ]
                ),
            },
        )
        _, pipeline_line = self.add_line(
            pipeline,
            self.env.ref("zbsync_files.model_zbs_dumper_file"),
            {
                "filepath": str(path) + "/{record.name}.csv",
            },
        )

        instance = pipeline.run_test()
        path.mkdir(exist_ok=True)
        instance._complete_run()

        file1 = path / "myname1.csv"
        data = instance._eval_data()
        self.assertEqual(data.record.name, "myname1")
        self.assertTrue(file1.exists())
        self.assertEqual((path / "myname1.csv").read_text().strip(), "anton")
