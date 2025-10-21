from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class FlowGroup(models.Model):
    _rec_name = "display_name"
    _name = "of.flow.group"
    _description = "Flows Flow-Group"

    name = fields.Char("Name", required=True)
    parent_id = fields.Many2one("of.flow.group", string="Parent")
    display_name = fields.Char(compute="_compute_name")

    def _compute_name(self):
        for rec in self:
            names = ((rec.parent_id and rec.parent_id.display_name) or "").split("/")
            names = list(map(lambda x: x.strip(), filter(bool, names)))
            names.append(rec.name)
            rec.display_name = " / ".join(names)
