from odoo import models, api

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []

        if not name:
            return super()._name_search(
                name=name,
                args=args,
                operator=operator,
                limit=limit,
                name_get_uid=name_get_uid,
            )

        domain = [
            "|", "|",
            ("name", "=ilike", f"{name}%"),
            ("default_code", "=ilike", f"{name}%"),
            ("barcode", "=ilike", f"{name}%"),
        ]

        return self._search(args + domain, limit=limit, access_rights_uid=name_get_uid)
