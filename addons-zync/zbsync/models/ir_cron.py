# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import api, fields, models


class IrCron(models.Model):
    _inherit = "ir.cron"
    zbs_crontrigger_id = fields.Many2one("zbs.cronstart", string="ZBS Cron Trigger")

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if not val.get("model_id"):
                val["model_id"] = (
                    self.env["ir.model"]
                    .search(
                        [
                            (
                                "model",
                                "=",
                                self.env.context.get("active_model", "res.company"),
                            ),
                        ],
                        limit=1,
                    )
                    .id
                )
            if not val.get("code"):
                val["code"] = "# nothing"

            if not val.get("name"):
                val["name"] = "-"

        res = super().create(vals_list)
        res._set_code()
        for rec in res:
            if res.model_id.model == "zbs.cronstart":
                res.active = True
        return res

    @api.constrains("zbs_crontrigger_id")
    def _set_code(self):
        for rec in self:
            if not rec.zbs_crontrigger_id:
                continue
            rec.model_id = (
                self.env["ir.model"].search([("model", "=", "zbs.cronstart")]).id
            )
            rec.code = f"model.browse(" f"{rec.zbs_crontrigger_id.id})._start()"
            rec.zbs_crontrigger_id._update_names_in_cronjobs()
