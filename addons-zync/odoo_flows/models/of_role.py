from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class OfRole(models.Model):
    _name = "of.role"
    _description = "Flows Role"

    name = fields.Char("Name", required=True)
