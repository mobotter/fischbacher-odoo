from odoo import api, fields, models, _

class CategoryCustom(models.Model):
    _inherit = 'product.category'

    category_number = fields.Char("Category Number")


    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                if category.category_number:
                    category.complete_name = '%s /[%s] %s' % (category.parent_id.complete_name, category.category_number, category.name)
                else:
                    category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                if category.category_number:
                    category.complete_name = '[%s] %s' % (category.category_number, category.name)
                else:
                    category.complete_name = category.name