from odoo import http
from odoo.http import request

class DialogLayoutController(http.Controller):

    @http.route('/odoo_dialog_user_layout/get', type='jsonrpc', auth='user')
    def get_layout(self, key):
        return {}

    @http.route('/odoo_dialog_user_layout/set', type='jsonrpc', auth='user')
    def set_layout(self, key, values):
        return True

    @http.route('/odoo_dialog_user_layout/reset', type='jsonrpc', auth='user')
    def reset_layout(self, key):
        return True
