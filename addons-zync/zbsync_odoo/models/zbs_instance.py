# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from .. import odoorpc


class Instance(models.Model):
    _inherit = "zbs.instance"

    def _prepare_process_data(self, input):
        if isinstance(input, odoorpc.models.Model):
            return input
        return super()._prepare_process_data(input)
