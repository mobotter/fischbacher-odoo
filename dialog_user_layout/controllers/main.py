from odoo import http
from odoo.http import request

class DialogLayoutController(http.Controller):
    @http.route('/odoo_dialog_user_layout/get', type='jsonrpc', auth='user')
    def get_layout(self, key):
        return request.env.user.dialog_layouts_json or {}

    @http.route('/odoo_dialog_user_layout/set', type='jsonrpc', auth='user')
    def set_layout(self, key, values):
        user = request.env.user
        data = dict(user.dialog_layouts_json or {})
        data[key] = values
        user.sudo().write({'dialog_layouts_json': data})
        return True

    @http.route('/odoo_dialog_user_layout/reset', type='jsonrpc', auth='user')
    def reset_layout(self, key=None):
        user = request.env.user
        data = dict(user.dialog_layouts_json or {})
        if key:
            data.pop(key, None)
        else:
            data = {}
        user.sudo().write({'dialog_layouts_json': data})
        return True
