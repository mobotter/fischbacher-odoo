# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models
from pathlib import Path
import inspect
import os
from pathlib import Path

current_dir = Path(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)


class JWTAuthorizer(models.Model):
    _inherit = "zbs.receive.authorizer"

    api_spec = fields.Text("API Specs", compute="_get_api_spec")

    def _get_api_spec(self):
        for rec in self:
            rec.api_spec = (current_dir.parent / "data" / "api_spec.yaml").read_text()
