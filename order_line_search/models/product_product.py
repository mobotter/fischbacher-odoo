from odoo import models, fields, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_view_product_sale_order_lines(self):
        self.ensure_one()
        variant_ids = self.product_variant_ids.ids
        
        list_view_id = self.env.ref('order_line_search.view_order_line_tree_custom').id

        return {
            'name': _('Verkaufte Positionen'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'list,form,pivot,graph',
            'views': [(list_view_id, 'list'), (False, 'form'), (False, 'pivot'), (False, 'graph')],
            'domain': [('product_id', 'in', variant_ids)],
            'context': {
            }
        }

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_view_product_sale_order_lines(self):
        self.ensure_one()
        
        list_view_id = self.env.ref('order_line_search.view_order_line_tree_custom').id

        return {
            'name': _('Verkaufte Positionen'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'list,form,pivot,graph',
            'views': [(list_view_id, 'list'), (False, 'form'), (False, 'pivot'), (False, 'graph')],
            'domain': [('product_id', '=', self.id)],
            'context': {
                'default_product_id': self.id,
            }
        }
