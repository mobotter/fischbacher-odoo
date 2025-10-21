# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models, fields
from pathlib import Path


class WebdavGrabber(models.Model):
    _inherit = ["zbs.grabber"]
    _name = "zbs.grabber.webdav"
    _description = "Webdav Grabber"

    connection_id = fields.Many2one("zbs.connection.webdav", required=False)
    content_path = fields.Char("Content Path")
    local_path = fields.Char("Local Path")
    glob = fields.Char("Path Expression Glob", default="*")
    content_type = fields.Selection(
        [
            ("bytes", "Binary"),
            ("string", "Text"),
        ],
    )
    encoding = fields.Char("Encoding", default="UTF8")
    limit = fields.Integer("Limit", default=100)

    def _eval_filepath(self, path, record):
        return Path(path.format(record=record))

    def process_record(self, instance, index, record, data, errors=None):
        client = self.connection_id.connect()
        l = client.list(self.content_path, get_info=True)
        records = []
        client.download_sync(remote_path=self.content_path, local_path=self.local_path)
        path = self._eval_filepath(self.local_path, record)
        method = getattr(path, "glob")
        for i, file in enumerate(method(self.glob), 1):
            if file.is_dir():
                continue
            if self.limit and i >= self.limit:
                break
            if self.content_type == "bytes":
                content = file.read_bytes()
            else:
                content = file.read_text(encoding=self.encoding)
            records.append(
                {
                    "filepath": file,
                    "filename": file.name,
                    "content": content,
                }
            )
        return records
