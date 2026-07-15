from odoo import models, api
from odoo.osv import expression

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        if not name:
            return super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

        domain = expression.OR([
            [("name", "=ilike", f"{name}%")],
            [("ref", "=ilike", f"{name}%")],
            [("email", "=ilike", f"{name}%")],
        ])
        return self._search(expression.AND([args, domain]), limit=limit, access_rights_uid=name_get_uid)
