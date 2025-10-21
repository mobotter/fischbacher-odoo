# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import base64
import json
import tempfile
import os
import zipfile
from pathlib import Path

from odoo import models, fields


class Pipeline(models.Model):
    _inherit = "zbs.pipeline"

    module_data_xml_string = fields.Char(
        "Module Data XML String", compute="_compute_module_data_xml_string"
    )

    def _compute_module_data_xml_string(self):
        for rec in self:
            content = json.dumps(rec.dump(), indent=4)
            content = base64.encodebytes(content.encode("utf-8"))
            rec.module_data_xml_string = (
                '<function model="zbs.pipeline" name="_non_interactive_import_base64">'
                f'  <value eval="{content}"/>'
                "</function>"
            )
            # rec.module_data_xml_string = (
            #     f'env["zbs.pipeline"]._non_interactive_import_base64({content})'
            # )

    def _non_interactive_import_base64(self, content):
        content = base64.b64decode(content)
        content = json.loads(content)
        pipeline = self.env["zbs.pipeline"].load(content)
        return pipeline

    def _get_zipped_json(self):
        self.snapshot()

        parent_dir = Path(tempfile.mktemp(suffix=""))
        parent_dir.mkdir(exist_ok=True, parents=True)
        filename = ",".join(sorted(map(str, self.ids))) + ".zip"
        zipfile_path = parent_dir / filename
        os.chdir(parent_dir)

        with zipfile.ZipFile(zipfile_path, mode="w") as zipf:
            for rec in self:
                version = rec.version_ids.sorted()[0]
                content = version.content
                date = version.date.strftime("%Y%m%d_%H%M%S")
                file = parent_dir / f"{rec.id}-{rec.name}-{date}.json"
                file.write_text(content)
                zipf.write(file.name)
        return zipfile_path.read_bytes()

    def download(self):
        ids = self.ids
        str_ids = ",".join(map(str, ids))
        return {
            "type": "ir.actions.act_url",
            "url": f"/zync/download?ids={str_ids}",
            "target": "self",
        }
