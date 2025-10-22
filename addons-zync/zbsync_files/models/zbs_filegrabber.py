# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import subprocess
import glob
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from pathlib import Path
from functools import partial
from datetime import datetime
import shutil


class FileMixin(models.AbstractModel):
    _name = "zbs.file.mixin"
    _description = "ZBS File Mixin"
    recursive = fields.Boolean(
        "Search subfolders",
        help="Allows recursive searching for matching files in subfolders.",
    )
    filepath = fields.Text(
        "File Path",
        help="Should match desired file path. Eg. /**/path?/{record.filename}",
    )
    destination_path = fields.Char("Destination Path")
    action_after_read = fields.Selection(
        [
            ("delete", "Delete"),
            ("move", "Move"),
        ],
        default=False,
        help="Applied to all selected files",
    )

    def _eval_filepath(self, index, record, data):
        res = (
            self._eval_expression(
                self.filepath,
                index,
                record,
                data,
                input=self.env.context.get("zbs_prepared_input_data"),
                expects_string_if_oneline=True,
            )
            or ""
        )
        paths = list(map(lambda x: x.strip(), res.split(",")))
        return paths

    def _eval_destination_path(self, index, record, data):
        res = (
            self._eval_expression(
                self.destination_path,
                index,
                record,
                data,
                input=self.env.context.get("zbs_prepared_input_data"),
                expects_string_if_oneline=True,
            )
            or ""
        )
        return res

    @api.constrains("action_after_read", "destination_path")
    def _check_destination_path(self):
        for record in self:
            if record.action_after_read == "move" and not record.destination_path:
                raise ValidationError(
                    _(
                        "Destination Path is required when Action After Read is set to 'Move'."
                    )
                )


class FileGrabber(models.Model):
    _inherit = ["zbs.grabber", "zbs.file.mixin"]
    _name = "zbs.grabber.file"
    _description = "File Grabber"

    limit = fields.Integer(
        "File Limit", help="Maximum number of files to return. 0 is treated as NO LIMIT"
    )
    content_type = fields.Selection(
        [
            ("bytes", "Binary"),
            ("string", "Text"),
        ],
        default="bytes",
        help="Expected file content type. Usually binary",
    )
    encoding = fields.Char(
        "Encoding",
        # TODO update field so that it uses only existing encoding types (or creates new ones), rather than accepting raw text
        default="UTF8",
        help="Expected file content encoding",
    )

    create_date_before = fields.Text("Created before")
    create_date_after = fields.Text("Created after")

    def process_record(self, instance, index, record, data, errors=None):
        patterns = self._eval_filepath(index, record, data)
        files = []
        for pattern in patterns:
            for i, file in enumerate(glob.glob(pattern, recursive=self.recursive), 1):
                file = Path(file)
                if file.is_dir():
                    continue
                if self.limit and i >= self.limit:
                    break
                metadata = self._get_metadata(file)

                if not self._file_in_filter(file, metadata):
                    continue
                files.append({"metadata": metadata, "file": file})
                del metadata

        records = []
        for i, file in enumerate(files, 1):
            metadata = file["metadata"]
            file = file["file"]

            if self.content_type == "bytes":
                content = file.read_bytes()
            else:
                content = file.read_text(encoding=self.encoding)
            metadata.update(
                {
                    "filepath": file,
                    "filename": file.name,
                    "content": content,
                    "record_index": index,
                }
            )
            records.append(metadata)
        return records

    @api.model
    def _get_creation_date(self, filepath):
        if (
            subprocess.run(["uname"], capture_output=True, text=True).stdout.strip()
            == "Linux"
        ):
            result = subprocess.run(
                ["stat", "-c", "%W", filepath], capture_output=True, text=True
            )
        else:
            result = subprocess.run(
                ["stat", "-f", "%c", filepath], capture_output=True, text=True
            )
        return self._timestamp_to_date(result.stdout.strip())

    @api.model
    def _get_modification_date(self, filepath):
        if (
            subprocess.run(["uname"], capture_output=True, text=True).stdout.strip()
            == "Linux"
        ):
            result = subprocess.run(
                ["stat", "-c", "%Y", filepath], capture_output=True, text=True
            )
        else:
            result = subprocess.run(
                ["stat", "-f", "%m", filepath], capture_output=True, text=True
            )

        return self._timestamp_to_date(result.stdout.strip())

    @api.model
    def _timestamp_to_date(self, ts):
        # Get the timestamp and convert it to a readable date
        timestamp = int(ts)
        modification_date = datetime.fromtimestamp(timestamp)
        return modification_date

    def _get_metadata(self, file):
        s = file.stat()
        return {
            "creation_date": self._get_creation_date(file),
            "modification_date": self._get_modification_date(file),
        }

    def _file_in_filter(self, file, metadata):
        instance = self.env.context["zbs_instance"]
        objects = instance._get_default_objects({"data": {}, "record": {}})

        def X(code, expected_type):
            res = self.env["zbs.tools"]._exec_get_result(code, objects)
            if expected_type is not None:
                if not isinstance(res, expected_type):
                    raise ValueError(f"Expected {expected_type} got {res}")
            return res

        if self.create_date_before:
            if not metadata["creation_date"] < X(self.create_date_before, datetime):
                return False
        if self.create_date_after:
            if not metadata["creation_date"] > X(self.create_date_after, datetime):
                return False
        return True

    def process(self, instance, data, errors=None):
        res = super().process(instance, data, errors=errors)
        return instance.Result(
            res.data, after_commit=partial(self.after_commit, res.data, data)
        )

    def after_commit(self, files, input_data):
        if self.action_after_read == "delete":
            [file["filepath"].unlink() for file in files]
        elif self.action_after_read == "move":
            # TODO could be better optimised by first sorting the files by the associated record_index
            # files_per_record = {}
            for i, record in enumerate(input_data._iterate_records()):
                destination_path = self._eval_destination_path(i, record, input_data)
                for file in filter(lambda file: file["record_index"] == i, files):
                    shutil.move(file["filepath"], destination_path)
