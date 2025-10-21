# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import uuid
from odoo.tests.common import Form
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase
from pathlib import Path


class FileGrabber(ZBSPipelineCase):
    def test_file_grab_and_delete(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "File Grabber"
        pipeline = form.save()
        guid = str(uuid.uuid4())
        path = Path(f"/tmp/{guid}")
        file_grabber = self.add_line(
            pipeline,
            self.env.ref("zbsync_files.model_zbs_grabber_file"),
            {
                "filepath": str(path) + "/*.csv",
                "recursive": False,
                "action_after_read": "delete",
                "content_type": "string",
                "create_date_before": "return datetime.now() + timedelta(days=1)",
            },
        )

        instance = pipeline.run_test()

        path.mkdir(exist_ok=True)
        file1 = path / "i_should_not_exist_because_action_after_read_is_delete.csv"
        file1.write_text("here i am")
        instance._complete_run()
        self.assertFalse(file1.exists())

        data = instance._eval_data()
        self.assertEqual(data.filename, file1.name)

    def test_file_grab_and_move(self):
        form = Form(self.env["zbs.pipeline"])
        form.name = "File Grabber"
        pipeline = form.save()
        guid = str(uuid.uuid4())
        path = Path(f"/tmp/{guid}")
        destination_path = Path("/tmp/processed")
        self.add_line(
            pipeline,
            self.env.ref("zbsync_files.model_zbs_grabber_file"),
            {
                "filepath": str(path) + "/*.csv",
                "recursive": False,
                "action_after_read": "move",
                "destination_path": str(destination_path),
                "content_type": "string",
                "create_date_before": "return datetime.now() + timedelta(days=1)",
            },
        )

        path.mkdir(exist_ok=True)
        destination_path.mkdir(exist_ok=True)

        filename = "to_be_read_and_moved.csv"
        read_file = path / filename
        moved_file = destination_path / filename

        read_file.write_text("hello world")

        self.assertTrue(read_file.exists())
        if moved_file.exists():
            moved_file.unlink()

        instance = pipeline.run_test()
        instance._complete_run()

        self.assertFalse(read_file.exists())
        self.assertTrue(moved_file.exists())
        moved_file.unlink()

        data = instance._eval_data()
        self.assertEqual(data.filename, read_file.name)
