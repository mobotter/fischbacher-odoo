from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.addons.module_tools import get_subclasses


class AbstractBase(models.AbstractModel):
    _inherit = ["of.mixin.code", "mail.thread"]
    _name = "of.base.item.abstract"
    _description = "Flows Abstract Base"

    # required must be false - so that creation works
    item_id = fields.Many2one("of.base.item", required=False, ondelete="cascade")
    has_code = fields.Boolean(compute="_has_code")
    show_condition = fields.Boolean(compute="_show_condition")
    custom_data_repr = fields.Text(compute="_compute_custom_data_repr")

    def _compute_custom_data_repr(self):
        for rec in self:
            rec.custom_data_repr = ""

    def _show_condition(self):
        self.write({"show_condition": False})

    def _has_code(self):
        self.write({"has_code": False})

    def add_trigger(self):
        self.ensure_one()
        trigger = self.env["of.trigger"].create(
            {
                "flow_id": self.flow_id.id,
                "name": "trigger",
                "role_id": self.role_id.id,
            }
        )
        trigger.item_id.outgoing_ids = [
            [
                0,
                0,
                {
                    "to_id": self.item_id.id,
                },
            ]
        ]
        return trigger.open()

    def _heartbeat(self, instance_item, additional_data):
        self.ensure_one()
        instance_item.ensure_one()

    def open(self):
        item = self
        if item._name == "of.base.item":
            item = item.ref

        context = self.env.context or {}

        return {
            "view_type": "form",
            "res_id": item.id,
            "res_model": item._name,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
            "context": context,
        }

    def make_item(self):
        objclass = self.env.context["item_type"]
        vals = {
            "name": "new",
            "flow_id": self.flow_id.id,
            "role_id": self.role_id.id,
        }
        item = self.env[objclass].create(vals)
        self.outgoing_ids = [
            [
                0,
                0,
                {
                    "to_id": item.item_id.id,
                },
            ]
        ]
        act = item.open()
        act.setdefault("flags", {})
        # act['context']['form_view_initial_mode'] = 'edit'
        act["flags"]["initial_mode"] = "edit"

        return act

    def unlink(self):
        for rec in self:
            rec.item_id.unlink()
        return super().unlink()

    def walk_to_start(self, prev_conn=None):
        for conn in self.incoming_ids:
            if conn.from_id:
                yield (prev_conn, conn.from_id)
                yield from conn.from_id.walk_to_start(conn)
