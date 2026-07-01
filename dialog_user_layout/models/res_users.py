from odoo import models

class ResUsers(models.Model):
    _inherit = 'res.users'

    def action_reset_dialog_layouts(self):
        return True
