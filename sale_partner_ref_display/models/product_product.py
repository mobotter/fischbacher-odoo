from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|',
                ('default_code', operator, name),
                ('name', operator, name),
            ]
        products = self.search(domain + args, limit=limit)
        return products.name_get()

    def name_get(self):
        result = []
        for product in self:
            display = product.name or ''
            if product.default_code:
                display = f"{product.default_code} - {display}"
            result.append((product.id, display))
        return result
