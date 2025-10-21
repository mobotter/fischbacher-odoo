# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
from odoo import models


class JsonGrabber(models.Model):
    _inherit = ["zbs.grabber"]
    _name = "zbs.grabber.json"
    _description = "JSON Grabber"

    def process_record(self, instance, index, record, data, errors=None):
        if not record:
            return
        content = self._extract_content(record)
        return json.loads(content)
