# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import models


class ZBSPipelineDemux(models.Model):
    _inherit = "zbs.worker"
    _name = "zbs.demuxer"
    _description = "Demuxer"
