from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    dialog_layouts_json = fields.Json(string='Dialog Layouts', default=dict)

    @api.model
    def _get_current_user_dialog_layouts(self):
        user = self.env.user
        return user.dialog_layouts_json or {}

    def dialog_layout_get(self, key):
        self.ensure_one()
        return (self.dialog_layouts_json or {}).get(key, {})

    def dialog_layout_set(self, key, values):
        self.ensure_one()
        data = dict(self.dialog_layouts_json or {})
        data[key] = values
        self.sudo().write({'dialog_layouts_json': data})
        return True

    def dialog_layout_reset(self, key=None):
        self.ensure_one()
        data = dict(self.dialog_layouts_json or {})
        if key:
            data.pop(key, None)
        else:
            data = {}
        self.sudo().write({'dialog_layouts_json': data})
        return True
