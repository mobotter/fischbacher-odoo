# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

import requests
from odoo import api, models


class CallBase(models.AbstractModel):
    _name = "zbs.call_base"
    _description = "Zync Call Base"

    @api.model
    def _call_base(self):
        database_uuid = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(key="database.uuid", default=False)
        )

        count_pipelines = self.env["zbs.pipeline"].sudo().search_count([])

        companies = ",".join(self.env["res.company"].sudo().search([]).mapped("name"))

        requests.post(
            "https://odoo.zebroo.de/zyncback",
            json={
                "database_uuid": database_uuid,
                "company": companies,
                "count_pipelines": count_pipelines,
            },
        )
