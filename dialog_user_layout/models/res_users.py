from odoo import fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    dialog_layouts = fields.Json(string='Dialog Layouts')

    def action_reset_dialog_layouts(self):
        for user in self:
            user.write({'dialog_layouts': {}})
        return True
