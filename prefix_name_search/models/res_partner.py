from odoo import models, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        if name:
            operator = "=ilike"
            domain = ["|", ("name", operator, f"{name}%"), ("ref", operator, f"{name}%")]
            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
