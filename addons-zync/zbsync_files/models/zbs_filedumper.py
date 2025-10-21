# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models
import uuid
from pathlib import Path


class FileDumper(models.Model):
    _inherit = [
        "zbs.dumper",
    ]
    _name = "zbs.dumper.file"
    _description = "File Dumper"

    filepath = fields.Char(
        "Filepath",
        default="/tmp/a/b/{record.filename}.csv",
        help="You can use: {guid}, {any key of record})\nEg. /path/path2/{record.filename}",
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
            filepath.write_text(content)
        elif isinstance(content, bytes):
            filepath.write_bytes(content)
        else:
            raise NotImplementedError(content)
        return {"filepath": filepath, "record": record}
