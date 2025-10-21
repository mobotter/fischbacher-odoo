# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models
from pypdf import PdfReader


class OdooPdfReader(models.Model):
    _inherit = "zbs.grabber"
    _name = "zbs.grabber.pdfreader"
    _description = "Zync PDF-Reader"

    def process_record(self, instance, index, record, data, errors=None):
        if not record:
            return

        content = self._extract_content(record)
        if not content:
            return None

        stream = self._get_stream(content)
        reader = PdfReader(stream)
        pages = []

        for page in reader.pages:
            pages.append(page.extract_text())

        return {
            "filecontent": content,
            "pages": pages,
        }
