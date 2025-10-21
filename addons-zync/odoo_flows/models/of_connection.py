from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class Connection(models.Model):
    _inherit = ["of.mixin.code"]
    _name = "of.connection"
    _description = "Flows Connection"
    _order = "sequence"
    _rec_name = "display_name"

    from_id = fields.Many2one(
        "of.base.item", string="From", required=True, ondelete="cascade"
    )
    to_id = fields.Many2one(
        "of.base.item", string="To", required=False, ondelete="cascade"
    )
    condition_name = fields.Char("Condition Shortname")
    condition = fields.Char("Condition", default="True", required=True)
    sequence = fields.Integer("Sequence")
    to_item_type = fields.Char(related="to_id.item_type", string="To Item Type")
    to_name = fields.Char(related="to_id.name", string="To Name")
    to_role_id = fields.Many2one(related="to_id.role_id", string="To Role")
    from_item_type = fields.Char(related="from_id.item_type", string="From Item Type")
    from_name = fields.Char(related="from_id.name", string="From Name")
    from_role_id = fields.Many2one(related="from_id.role_id", string="From Role")

    display_name = fields.Char(compute="_compute_name")

    def open_line(self):
        view_id = self.env.ref("odoo_flows.connection_form_modal").id
        if self.env.context.get("connection_regular_form"):
            view_id = False
        return {
            "view_type": "form",
            "res_model": self._name,
            "res_id": self.id,
            "views": [(view_id, "form")],
            "type": "ir.actions.act_window",
            "target": "new",
            "context": {
                "default_flow_id": self.from_id.flow_id.id,
            },
        }

    def open(self):
        obj = None
        if self.env.context.get("inout") == "out":
            obj = self.to_id
        else:
            obj = self.from_id
        if obj:
            return obj.open()
        return True

    def open_to(self):
        return self.to_id.open()

    def open_from(self):
        return self.from_id.open()

    @api.depends_context("connection_display_type")
    def _compute_name(self):
        for rec in self:
            if self.env.context.get("connection_display_type") == "incoming":
                rec.display_name = rec.from_id.name
            elif self.env.context.get("connection_display_type") == "outgoing":
                rec.display_name = rec.to_id.name
            else:
                rec.display_name = f"{rec.from_id.name}" " -> " f"{rec.to_id.name}"

    def unlink_connection(self):
        pass

    def _get_eval_objects(self, instance_item):
        return dict(
            instance=instance_item,
            object=instance_item,
            obj=instance_item,
            instance_item=instance_item,
            code_field="condition",
        )

    def applies(self, instance_item):
        eval_objects = self._get_eval_objects(instance_item)
        result = self._eval(**eval_objects)
        return bool(result)

    def ok(self):
        return {"type": "ir.actions.act_window_close"}
