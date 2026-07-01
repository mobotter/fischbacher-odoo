from odoo import models

class ResUsers(models.Model):
    _inherit = 'res.users'

    def action_reset_dialog_layouts(self):
        self.env['ir.config_parameter'].sudo().set_param('dialog_user_layout.reset_trigger', '1')
        return True
