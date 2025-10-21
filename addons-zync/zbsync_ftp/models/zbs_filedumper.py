# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models
from odoo.exceptions import ValidationError
import uuid
from pathlib import Path


class FileDumper(models.Model):
    _inherit = [
        "zbs.dumper",
    ]
    _name = "zbs.dumper.file.ftp"
    _description = "FTP Dumper"

    connection_id = fields.Many2one("zbs.connection.ftp", string="FTP Host")
    encoding_id = fields.Many2one("zbs.encoding", string="Encoding as text")
    filepath = fields.Char(
        "Filepath",
        default="/tmp/a/b/{record.filename}.csv",
        help="You can use: {guid}, {any key of record})",
    )

    def process_record(self, instance, index, record, data, errors=None):
        self = self.with_context(instance=instance)

        vars = {
            "guid": str(uuid.uuid4()),
            "record": record,
        }
        filepath = Path(self.filepath.format(**vars))
        content = self._extract_content(record)

        if isinstance(content, str):
            if not self.encoding_id:
                raise ValidationError("Please set an encoding for storing text!")
            content = content.encode(self.encoding_id.name)
        ftp = self.connection_id.ftpObject
        with ftp.connect():
            ftp.upload_file(filepath, content)
        return {"filepath": filepath, "record": record}
