# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import models


class ZBSGrabber(models.AbstractModel):
    _inherit = ["zbs.worker", "zbs.grabber_dumper"]
    _name = "zbs.grabber"
    _description = "Common Grabber"
