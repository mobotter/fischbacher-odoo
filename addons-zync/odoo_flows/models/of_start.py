from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class Start(models.Model):
    _inherit = ["of.base.item.abstract"]
    _inherits = {"of.base.item": "item_id"}
    _name = "of.start"
    _description = "Flows Start"

    item_id = fields.Many2one("of.base.item", auto_join=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault("name", "Start")
        res = super().create(vals_list)
        return res

    def _heartbeat(self, instance_item, additional_data):
        super()._heartbeat(instance_item, additional_data)
        instance_item._goto_next()
