from odoo import api, models, _
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.constrains("default_code")
    def _check_unique_default_code(self):
        for record in self:
            code = (record.default_code or "").strip()
            if not code:
                continue

            duplicate = self.search([
                ("id", "!=", record.id),
                ("default_code", "=", code),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    _("Variant Internal Reference '%s' already exists.") % code
                )
