from odoo import http
from odoo.http import request

class DialogLayoutController(http.Controller):

    @http.route('/odoo_dialog_user_layout/get', type='jsonrpc', auth='user')
    def get_layout(self, key):
        layouts = request.env.user.sudo().dialog_layouts or {}
        return {key: layouts.get(key)}

    @http.route('/odoo_dialog_user_layout/set', type='jsonrpc', auth='user')
    def set_layout(self, key, values):
        user = request.env.user.sudo()
        layouts = dict(user.dialog_layouts or {})
        layouts[key] = values
        user.write({'dialog_layouts': layouts})
        return True

    @http.route('/odoo_dialog_user_layout/reset', type='jsonrpc', auth='user')
    def reset_layout(self, key):
        user = request.env.user.sudo()
        layouts = dict(user.dialog_layouts or {})
        layouts.pop(key, None)
        user.write({'dialog_layouts': layouts})
        return True
