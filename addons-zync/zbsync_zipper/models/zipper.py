# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import zipfile
from pathlib import Path
import tempfile
from odoo import fields, models
import shutil


class Zipper(models.Model):
    _inherit = "zbs.grabber"
    _name = "zbs.grabber.zipper"
    _description = "ZIPFile Grabber"

    glob = fields.Char()

    def process_record(self, instance, index, record, data, errors=None):
        if not record:
            return

        content = self._extract_content(record)
        if not content:
            return None

        filepath = Path(tempfile._get_default_tempdir()) / next(
            tempfile._get_candidate_names()
        )

        filepath.mkdir(exist_ok=True, parents=True)
        zip_file_path = filepath / "archive.zip"
        extract_to_directory = filepath / "out"
        try:
            zip_file_path.write_bytes(content)

            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                # Extract all contents into the specified directory
                zip_ref.extractall(extract_to_directory)

            res = []
            for file in extract_to_directory.rglob(self.glob or "*"):
                if file.is_dir():
                    continue
                content = file.read_bytes()
                res.append(
                    {
                        "filename": file.name,
                        "filepath": str(file.relative_to(extract_to_directory)),
                        "filecontent": content,
                    }
                )
        finally:
            shutil.rmtree(filepath)

        return res
