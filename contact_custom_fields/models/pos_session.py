from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        domain = result["search_params"].get("domain", [])
        result["search_params"]["domain"] = domain + [("sale_blocked", "=", False)]
        return result
