from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends('default_code', 'name')
    def _compute_display_name(self):
        for product in self:
            name = product.name or ''
            product.display_name = f"{product.default_code} - {name}" if product.default_code else name

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = list(args or [])
        if name:
            args = ['|', ('default_code', operator, name), ('name', operator, name)] + args
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
