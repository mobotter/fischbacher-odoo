# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import re
from odoo import fields, models
from pathlib import Path
from functools import partial


class FileGrabber(models.Model):
    _inherit = ["zbs.grabber", "zbs.file.mixin"]
    _name = "zbs.grabber.file.ftp"
    _description = "FTP Grabber"

    connection_id = fields.Many2one("zbs.connection.ftp", string="FTP Host")
    filter_type = fields.Selection(
        [
            ("regex", "Regex"),
            ("wildcard", "Wildcard"),
        ],
        required=True,
        default="regex",
    )
    regex_filter = fields.Char("Regex Filter")
    wildcard_filter = fields.Char("Wildcard Filter")
    limit = fields.Integer("Limit Files")
    encoding_id = fields.Many2one("zbs.encoding", string="Encoding as text")

    def process_record(self, instance, index, record, data, errors=None):
        ftp = self.connection_id.ftpObject
        with ftp.connect():
            filepath = self._eval_filepath(index, record, data)
            records = []
            for path in filepath:
                files = ftp.list_files(path=path, recursive=self.recursive)

                Filter = ""
                if self.filter_type == "wildcard" and self.wildcard_filter:
                    Filter = self.wildcard_filter.replace("*", ".*")

                if self.filter_type == "regex" and self.regex_filter:
                    Filter = self.regex_filter

                if Filter:

                    def matchit(path):
                        return bool(re.findall(Filter, path))

                    files = list(filter(matchit, files))

                for i, file in enumerate(files, 1):
                    if self.limit and i >= self.limit:
                        break

                    content = ftp.download_file(file)
                    if self.encoding_id:
                        content = content.decode(self.encoding_id.name)
                    records.append(
                        {
                            "filepath": file,
                            "filename": Path(file).name,
                            "content": content,
                            "record_index": index,
                        }
                    )
        return records

    def process(self, instance, data, errors=None):
        res = super().process(instance, data, errors=errors)
        files = []
        for rec in res.data:
            files.append(rec)
        return instance.Result(
            files, after_commit=partial(self.after_commit, files, data)
        )

    def after_commit(self, files, input_data):
        if self.action_after_read == "delete":
            ftp = self.connection_id.ftpObject
            with ftp.connect():
                for file in files:
                    ftp.delete_file(file["filepath"])

        elif self.action_after_read == "move":
            ftp = self.connection_id.ftpObject
            with ftp.connect():
                # TODO could be better optimised by first sorting the files by the associated record_index
                # files_per_record = {}
                for i, record in enumerate(input_data._iterate_records()):
                    destination_path = self._eval_destination_path(
                        i, record, input_data
                    )
                    for file in filter(lambda file: file["record_index"] == i, files):
                        ftp.move_ftp_file(file["filepath"], destination_path)
