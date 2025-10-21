from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.addons.module_tools import get_subclasses
from odoo.tools import OrderedSet
import inspect
import os
from pathlib import Path

current_dir = Path(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)


class Base(models.Model):
    _inherit = ["of.base.item.abstract"]
    _name = "of.base.item"
    _description = "Flows Base Item"

    item_id = fields.Many2one("of.base.item", required=False)
    split_away = fields.Boolean("Branch away")
    flow_id = fields.Many2one("of.flow", required=True)
    name = fields.Char("Name", required=True)
    desc = fields.Text("Description")
    ref = fields.Reference(
        selection="_compute_refs", compute="_compute_ref", store=False
    )
    incoming_ids = fields.One2many(
        "of.connection", "to_id", string="Incomings", copy=False
    )
    outgoing_ids = fields.One2many(
        "of.connection", "from_id", string="Outgoings", copy=False
    )
    role_id = fields.Many2one("of.role", string="Role", required=True)
    shape_type = fields.Selection(
        [
            ("rhombus", "Rhombus"),
            ("ellipse", "Ellipse"),
            ("parallelogram", "Parallelogram"),
            ("hexagon", "Hexagon"),
            ("rounded", "Rounded"),
            ("diamond", "Diamond"),
            ("circle", "Circle"),
            ("square", "Square"),
            ("box", "Box"),
            ("dot", "Dot"),
            ("star", "Start"),
            ("triangle", "Triangle"),
            ("triangleDown", "Triangle Down"),
        ]
    )
    background_color = fields.Char("Color", compute="_compute_chartinfos")
    item_type = fields.Char("Type", compute="_compute_type")
    sequence = fields.Integer("Sequence")
    deadline_days = fields.Float("Deadline Days", default=1)
    outgoing_text = fields.Char("Outgoing", compute="_compute_text")
    incoming_text = fields.Char("Incoming", compute="_compute_text")
    no_deadline = fields.Boolean("No Deadline")
    node_name = fields.Char(compute="_compute_node_name")

    def _compute_node_name(self):
        for rec in self:
            name = ""
            classname = rec.ref._name.split(".")[-1]
            if rec.name:
                name += rec.name
                if classname.lower() != rec.name.lower():
                    name += f" ({classname})"
            else:
                name += classname
            rec.node_name = name

    def _compute_text(self):
        for rec in self:
            rec.outgoing_text = ", ".join(rec.mapped("outgoing_ids.to_id.name"))
            rec.incoming_text = ", ".join(rec.mapped("incoming_ids.from_id.name"))

    def _compute_chartinfos(self):
        content = (current_dir / "flow_defaults.txt").read_text().splitlines()
        for rec in self:
            if rec.ref:
                style = [x for x in content if x.startswith(f"{rec.ref._name}:")]
                if not style:
                    raise ValidationError(f"Missing: {rec.ref._name}")
                model, shape, color = style[0].split(":", 2)
                rec.shape_type = shape
                rec.background_color = color

    def _compute_type(self):
        for rec in self:
            rec.item_type = rec.ref._name

    def _compute_refs(self):
        subs = list(get_subclasses(self.env, self._name))
        return [(x, x) for x in subs]

    def _compute_ref(self):
        subs = get_subclasses(self.env, "of.base.item")
        for rec in self:
            for obj in subs:
                obj = self.env[obj].sudo().search([("item_id", "=", rec.id)], limit=1)
                if obj:
                    rec.ref = obj
                    break
                else:
                    rec.ref = False
