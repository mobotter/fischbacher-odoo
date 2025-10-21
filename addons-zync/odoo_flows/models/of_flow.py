from odoo import _, api, fields, models, SUPERUSER_ID
import json
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import inspect
import os
from pathlib import Path

current_dir = Path(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)


class Flow(models.Model):
    _name = "of.flow"
    _description = "Flows Flow"

    active = fields.Boolean("Active", default=True)
    group_id = fields.Many2one("of.flow.group", string="Group")
    name = fields.Char("Name", required=True)
    item_ids = fields.One2many("of.base.item", "flow_id", string="Items")
    instance_ids = fields.One2many("of.instance", "flow_id", string="Instances")
    diagram_content = fields.Text(
        compute="_compute_diagram_vis", store=False, readonly=False
    )
    model_id = fields.Many2one(
        "ir.model", string="Model", required=True, ondelete="cascade"
    )
    allow_concurrency_runs = fields.Boolean("Allow Concurrency Runs")
    priority = fields.Integer("Queuejob Priority")

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record.make_basic_items()
        return res

    def make_basic_items(self):
        for rec in self:
            rec = rec.with_context(default_flow_id=rec.id)
            default_role = self.env["of.role"].search([], limit=1)
            if not default_role:
                raise ValidationError("Please define a role")
            start = rec.env["of.start"].create(
                {
                    "role_id": default_role.id,
                }
            )
            end = rec.env["of.end"].create(
                {
                    "role_id": default_role.id,
                }
            )

    def start_from_ui(self):
        instance = self.start()
        return {
            "view_type": "form",
            "res_model": instance._name,
            "res_id": instance.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "context": {
                "form_view_initial_mode": "edit",
            },
            "target": "current",
        }

    def start(self, obj=None):
        self.ensure_one()
        ref = f"{obj._name},{obj.id}" if obj else False

        instance = False
        if ref:
            instance = self.instance_ids.search(
                [
                    ("initial_odoo_instance", "=", ref),
                    ("flow_id", "=", self.id),
                ],
                limit=1,
            )
        if not instance or self.allow_concurrency_runs:
            instance = self.instance_ids.create(
                {"flow_id": self.id, "initial_odoo_instance": ref}
            )
            instance._start(obj)
        return instance

    @api.model
    def _cron_heartbeat(self):
        for rec in self.search([]):
            rec.with_context(is_cron=True).heartbeat()

    @api.model
    def _cron_check_triggers(self):
        for rec in self.search([]):
            rec.check_triggers()

    def heartbeat(self):
        self.ensure_one()
        for instance in self.instance_ids:
            with instance.semaphore_with_delay(priority=self.priority) as instance:
                if instance:
                    instance.heartbeat()

    def check_triggers(self):
        self.ensure_one()
        for trigger in self.item_ids.filtered(lambda x: x.ref._name == "of.trigger"):
            trigger.ref._heartbeat()

    def _compute_diagram_vis(self):
        for record in self:
            nodes, edges = [], []
            for node in self.item_ids:
                nodes.append(
                    {
                        "id": node.id,
                        "label": node.node_name,
                        "title": node.desc or node.name,
                        "shape": node.shape_type,
                        "color": node.background_color,
                        "onclick": {
                            "model": node._name,
                            "res_id": node.id,
                            "method": "open",
                        },
                    }
                )
                for outgoing in node.outgoing_ids:
                    edges.append(
                        {
                            "id": -outgoing.id,
                            "from": node.id,
                            "to": outgoing.to_id.id,
                            "arrows": "to",
                            "label": outgoing.condition_name or outgoing.condition,
                            "onclick": {
                                "model": "of.connection",
                                "res_id": outgoing.id,
                                "method": "open_line",
                            },
                        }
                    )

            record.diagram_content = json.dumps(
                {
                    "res_id": record.id,
                    "nodes": nodes,
                    "edges": edges,
                    "selected_ids": [],
                }
            )
            print(json.dumps(json.loads(record.diagram_content), indent=4))

    @api.model
    def _get_diagram_head(self):
        content = (current_dir / "flow_style.txt").read_text().strip()
        return content

    def format_field(self, field):
        if field is None:
            return ""
        if isinstance(field, list) and field and isinstance(field[0], int):
            field = ",".join(map(str, field))
        try:
            int(field)
        except Exception:
            field = field.replace('"', "'")
            return f'"{field}"'
        else:
            return str(field)

    def format_line(self, line):
        return ",".join(map(self.format_field, line))

    def _get_diagram_lines(self):
        lines = []
        self.ensure_one()
        for role in self.mapped("item_ids.role_id"):
            if not role:
                continue
            lines.append(
                [
                    role.name,
                    -1 * role.id,
                    None,
                    None,
                    None,
                    "tswimlane",
                ]
            )

        for i, item in enumerate(self.item_ids):
            if item.name:
                lines.append(
                    [
                        item.name,
                        item.id,
                        -1 * (item.role_id.id or 0),
                        item.outgoing_ids.mapped("to_id").ids or "",
                        item.incoming_ids.mapped("from_id").ids or "",
                        item.ref.shape_type,
                        item.ref.background_color or "#FFF",
                        "1",
                    ]
                )
        return lines
