from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class End(models.Model):
    _inherit = ["of.base.item.abstract"]
    _inherits = {"of.base.item": "item_id"}
    _name = "of.end"
    _description = "Flows End"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault("name", "End")
        res = super().create(vals_list)
        return res

    @api.model
    def _chart(self):
        return {
            "shape_type": "ellipsis",
            "background_color": "#ccc",
        }
