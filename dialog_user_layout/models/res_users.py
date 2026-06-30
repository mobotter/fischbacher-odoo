from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    dialog_layouts_json = fields.Json(string='Dialog Layouts', default=dict)
