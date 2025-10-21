# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from .. import odoorpc


class InstanceLine(models.Model):
    _inherit = "zbs.instance.line"

    def _append_data(self, index, container, item):
        if isinstance(item, odoorpc.models.Model):
            if not index:
                return item
            else:
                return container.browse(container.ids + item.ids)

        return super()._append_data(index, container, item)
