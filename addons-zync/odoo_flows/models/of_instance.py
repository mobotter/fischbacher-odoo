import json
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError

# from odoo.addons.queue_job.job import job


class Instance(models.Model):
    _inherit = ["mixin.queuejob.semaphore"]
    _name = "of.instance"
    _description = "Flows Instance"
    _order = "id desc"

    active = fields.Boolean(default=lambda self: True)
    flow_id = fields.Many2one(
        "of.flow", string="Flow", ondelete="cascade", required=True
    )
    item_ids = fields.One2many("of.instance.item", "instance_id", string="Items")
    name = fields.Char("Name", compute="_compute_name", store=True, readonly=True)
    initial_odoo_instance = fields.Char("Odoo Instance")
    diagram_content = fields.Text(compute="_compute_diagram")
    manual_mode = fields.Boolean("Manual Mode")
    odoo_instance_name = fields.Char(compute="_compute_odoo_instance")
    was_started_with_instance = fields.Boolean(default=True)

    def _compute_odoo_instance(self):
        for rec in self:
            oi = rec.odoo_instance
            if oi:
                rec.odoo_instance_name = oi.name_get()[0][1]
            else:
                rec.odoo_instance_name = "-"

    def abort(self):
        self.active = False

    def open_odoo_instance(self):
        return {
            "view_type": "form",
            "res_model": self.odoo_instance._name,
            "res_id": self.odoo_instance.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    @property
    def odoo_instance(self):
        self.ensure_one()
        if not self.initial_odoo_instance:
            return False
        model, id = self.initial_odoo_instance.split(",")
        id = int(id)
        return self.env[model].browse(id)

    def restart(self):
        self.item_ids.sudo().unlink()
        self.active = True
        self._start(self.odoo_instance)

    def _start(self, obj):
        self.was_started_with_instance = bool(obj)
        start_item = self.flow_id.item_ids.filtered(lambda x: x.ref._name == "of.start")
        if not start_item:
            raise ValidationError("No start found")
        if obj and obj._name not in self.mapped("flow_id.model_id.model"):
            raise ValidationError("Not allowed model")
        start_instance_item = self.env["of.instance.item"]._make_item(
            self, start_item, obj
        )
        start_instance_item.has_cursor = True

    def heartbeat(self):
        for rec in self:
            if rec.manual_mode and self.env.context.get("is_cron"):
                continue
            for item in rec.item_ids.filtered(lambda x: x.has_cursor):
                item._heartbeat()

    @api.depends(
        "flow_id.name",
    )
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.flow_id.name}-" f"{rec.id}"

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        return res

    def _compute_is_done(self):
        for rec in self:
            # multi stops possible
            actives = list(
                set(
                    x.item_id.ref._name
                    for x in rec.item_ids.filtered(lambda x: x.has_cursor)
                )
            )
            rec.active = not (len(actives) == 1 and actives[0] == "of.end")

    def _compute_diagram(self):
        for rec in self:
            content = json.loads(rec.flow_id.diagram_content or "{}")
            active = rec.item_ids.filtered(lambda x: x.has_cursor).item_id.ids
            content["selected_ids"] = active
            rec.diagram_content = json.dumps(content)

    def open_diagram_item(self, item_id, model):
        return self.flow_id.open_diagram_item(item_id, model)

    def get_item(self, base_item_model, base_item_id):
        base_item = self.env[base_item_model].sudo().browse(base_item_id).item_id
        item = self.item_ids.filtered(lambda x: x.item_id == base_item)
        return item
